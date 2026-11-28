package compiler

// AC-013-01 isolated PoC: Schema-driven author-expression guard checking and
// lowering to a typed wire AST that cel-go checks and cel-expr-python loads.
//
// This file lives only in the isolated evidence copy. It reuses the real
// buildSchemaRegistry / resolveReferenceFrom / resolveSchemaRoot path and the
// multi-Skill shared Lock fixture; it does not modify any frozen contract.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"

	"cel.dev/cel-go/cel"
	"cel.dev/cel-go/common/ast"
	celpb "cel.dev/expr"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
	"google.golang.org/protobuf/types/known/anypb"

	yaml "github.com/odango-chan/ca-skill-compiler/internal/compiler/yamlast"
)

// ---------- G.4 schema model ----------

type g4Field struct {
	name     string
	optional bool
	nullable bool
	kind     string // string, int, double, bool, object, array
	nested   *g4Object
	item     *g4Field
}

type g4Object struct {
	name   string
	fields []*g4Field
	byName map[string]*g4Field
}

func (o *g4Object) field(name string) *g4Field { return o.byName[name] }

func schemaTypeNames(node *yaml.Node) ([]string, bool) {
	typeNode := child(node, "type")
	if typeNode == nil {
		return nil, false
	}
	switch typeNode.Kind {
	case yaml.ScalarNode:
		return []string{scalar(typeNode)}, true
	case yaml.SequenceNode:
		names := []string{}
		for _, item := range sequence(typeNode) {
			names = append(names, scalar(item))
		}
		return names, true
	}
	return nil, false
}

func requiredSet(node *yaml.Node) map[string]bool {
	set := map[string]bool{}
	for _, item := range sequence(child(node, "required")) {
		set[scalar(item)] = true
	}
	return set
}

// parseG4Object converts a resolved G.4 Schema node into the PoC object model.
func parseG4Object(registry schemaRegistry, resource schemaResource, name string, depth int) (*g4Object, error) {
	if depth > 16 {
		return nil, fmt.Errorf("schema nesting too deep at %s", name)
	}
	// Follow a root $ref first.
	if ref := child(resource.node, "$ref"); ref != nil {
		target, problem := registry.resolveReferenceFrom(resource, scalar(ref))
		if problem != "" {
			return nil, fmt.Errorf("resolve %s: %s", scalar(ref), problem)
		}
		effective, problem := registry.resolveSchemaRoot(target)
		if problem != "" {
			return nil, fmt.Errorf("resolve root %s: %s", scalar(ref), problem)
		}
		return parseG4Object(registry, effective, name, depth+1)
	}
	names, ok := schemaTypeNames(resource.node)
	if !ok || len(names) != 1 || names[0] != "object" {
		return nil, fmt.Errorf("%s: PoC expects a closed object schema, got %v", name, names)
	}
	obj := &g4Object{name: name, byName: map[string]*g4Field{}}
	props := child(resource.node, "properties")
	required := requiredSet(resource.node)
	if props == nil || props.Kind != yaml.MappingNode {
		return obj, nil
	}
	for i := 0; i+1 < len(props.Content); i += 2 {
		fieldName := scalar(unalias(props.Content[i]))
		fieldNode := unalias(props.Content[i+1])
		fieldResource := schemaResource{identity: resource.identity + "#" + fieldName, node: fieldNode}
		field, err := parseG4Field(registry, fieldResource, fieldName, depth+1)
		if err != nil {
			return nil, err
		}
		field.optional = !required[fieldName]
		obj.fields = append(obj.fields, field)
		obj.byName[fieldName] = field
	}
	sort.Slice(obj.fields, func(i, j int) bool { return obj.fields[i].name < obj.fields[j].name })
	return obj, nil
}

func parseG4Field(registry schemaRegistry, resource schemaResource, name string, depth int) (*g4Field, error) {
	if ref := child(resource.node, "$ref"); ref != nil {
		target, problem := registry.resolveReferenceFrom(resource, scalar(ref))
		if problem != "" {
			return nil, fmt.Errorf("resolve %s: %s", scalar(ref), problem)
		}
		effective, problem := registry.resolveSchemaRoot(target)
		if problem != "" {
			return nil, fmt.Errorf("resolve root %s: %s", scalar(ref), problem)
		}
		return parseG4Field(registry, effective, name, depth+1)
	}
	names, ok := schemaTypeNames(resource.node)
	if !ok {
		return nil, fmt.Errorf("field %s has no supported type", name)
	}
	nullable := false
	if len(names) == 2 {
		if names[1] == "null" {
			nullable = true
			names = names[:1]
		} else if names[0] == "null" {
			nullable = true
			names = names[1:]
		}
	}
	if len(names) != 1 {
		return nil, fmt.Errorf("field %s: unsupported union %v", name, names)
	}
	field := &g4Field{name: name, nullable: nullable}
	switch names[0] {
	case "string":
		field.kind = "string"
	case "integer":
		field.kind = "int"
	case "number":
		field.kind = "double"
	case "boolean":
		field.kind = "bool"
	case "object":
		nested, err := parseG4Object(registry, resource, name, depth)
		if err != nil {
			return nil, err
		}
		field.kind = "object"
		field.nested = nested
	case "array":
		itemNode := unalias(child(resource.node, "items"))
		itemResource := schemaResource{identity: resource.identity + "[]", node: itemNode}
		item, err := parseG4Field(registry, itemResource, name+"Item", depth+1)
		if err != nil {
			return nil, err
		}
		field.kind = "array"
		field.item = item
	default:
		return nil, fmt.Errorf("field %s: unsupported type %q", name, names[0])
	}
	return field, nil
}

// ---------- descriptor generation ----------

type descBuilder struct {
	pkg    string
	file   *descriptorpb.FileDescriptorProto
	next   int
	wraps  int
	events bool
}

func (b *descBuilder) messageName(parent, field string) string {
	name := parent + strings.ToUpper(field[:1]) + field[1:]
	return name
}

func scalarFieldType(kind string) descriptorpb.FieldDescriptorProto_Type {
	switch kind {
	case "string":
		return descriptorpb.FieldDescriptorProto_TYPE_STRING
	case "int":
		return descriptorpb.FieldDescriptorProto_TYPE_INT64
	case "double":
		return descriptorpb.FieldDescriptorProto_TYPE_DOUBLE
	case "bool":
		return descriptorpb.FieldDescriptorProto_TYPE_BOOL
	}
	return descriptorpb.FieldDescriptorProto_TYPE_MESSAGE
}

// emitObject appends the message for obj (and nested/wrapper messages) to the file.
func (b *descBuilder) emitObject(obj *g4Object) *descriptorpb.DescriptorProto {
	msg := &descriptorpb.DescriptorProto{Name: proto.String(obj.name)}
	number := int32(0)
	for _, field := range obj.fields {
		number++
		if field.nullable {
			wrapperName := obj.name + b.messageName("", field.name) + "Nullable"
			fd := &descriptorpb.FieldDescriptorProto{
				Name:     proto.String(field.name),
				Number:   proto.Int32(number),
				Type:     descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum(),
				TypeName: proto.String("." + b.pkg + "." + wrapperName),
				Label:    descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
			}
			msg.Field = append(msg.Field, fd)
			b.file.MessageType = append(b.file.MessageType, b.wrapperMessage(wrapperName, field))
			continue
		}
		fd := &descriptorpb.FieldDescriptorProto{
			Name:   proto.String(field.name),
			Number: proto.Int32(number),
			Label:  descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
		}
		switch field.kind {
		case "object":
			childName := obj.name + b.messageName("", field.name)
			fd.Type = descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum()
			fd.TypeName = proto.String("." + b.pkg + "." + childName)
			msg.Field = append(msg.Field, fd)
			b.file.MessageType = append(b.file.MessageType, b.emitObject(&g4Object{name: childName, fields: field.nested.fields, byName: field.nested.byName}))
		case "array":
			fd.Label = descriptorpb.FieldDescriptorProto_LABEL_REPEATED.Enum()
			if field.item.kind == "object" {
				childName := obj.name + b.messageName("", field.name+"Item")
				fd.Type = descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum()
				fd.TypeName = proto.String("." + b.pkg + "." + childName)
				b.file.MessageType = append(b.file.MessageType, b.emitObject(&g4Object{name: childName, fields: field.item.nested.fields, byName: field.item.nested.byName}))
			} else {
				fd.Type = scalarFieldType(field.item.kind).Enum()
			}
			msg.Field = append(msg.Field, fd)
		default:
			fd.Type = scalarFieldType(field.kind).Enum()
			msg.Field = append(msg.Field, fd)
		}
	}
	return msg
}

func (b *descBuilder) wrapperMessage(name string, field *g4Field) *descriptorpb.DescriptorProto {
	msg := &descriptorpb.DescriptorProto{
		Name:      proto.String(name),
		OneofDecl: []*descriptorpb.OneofDescriptorProto{{Name: proto.String("state")}},
	}
	if field.kind == "object" {
		childName := name + "Value"
		msg.Field = append(msg.Field, &descriptorpb.FieldDescriptorProto{
			Name: proto.String("value"), Number: proto.Int32(1),
			Type: descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum(),
			TypeName: proto.String("." + b.pkg + "." + childName),
			Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
			OneofIndex: proto.Int32(0),
		})
		b.file.MessageType = append(b.file.MessageType, b.emitObject(&g4Object{name: childName, fields: field.nested.fields, byName: field.nested.byName}))
	} else if field.kind == "array" {
		childName := name + "Value"
		inner := &descriptorpb.DescriptorProto{Name: proto.String(childName), Field: []*descriptorpb.FieldDescriptorProto{{
			Name: proto.String("items"), Number: proto.Int32(1),
			Label: descriptorpb.FieldDescriptorProto_LABEL_REPEATED.Enum(),
			Type:  scalarFieldType(field.item.kind).Enum(),
		}}}
		msg.Field = append(msg.Field, &descriptorpb.FieldDescriptorProto{
			Name: proto.String("value"), Number: proto.Int32(1),
			Type: descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum(),
			TypeName: proto.String("." + b.pkg + "." + childName),
			Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
			OneofIndex: proto.Int32(0),
		})
		b.file.MessageType = append(b.file.MessageType, inner)
	} else {
		msg.Field = append(msg.Field, &descriptorpb.FieldDescriptorProto{
			Name: proto.String("value"), Number: proto.Int32(1),
			Type: scalarFieldType(field.kind).Enum(),
			Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
			OneofIndex: proto.Int32(0),
		})
	}
	msg.Field = append(msg.Field, &descriptorpb.FieldDescriptorProto{
		Name: proto.String("is_null"), Number: proto.Int32(2),
		Type: descriptorpb.FieldDescriptorProto_TYPE_BOOL.Enum(),
		Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
		OneofIndex: proto.Int32(0),
	})
	return msg
}

func (b *descBuilder) build(input *g4Object) *descriptorpb.FileDescriptorSet {
	file := &descriptorpb.FileDescriptorProto{
		Name:    proto.String(b.pkg + ".proto"),
		Package: proto.String(b.pkg),
		Syntax:  proto.String("proto2"),
	}
	b.file = file
	file.MessageType = append(file.MessageType, b.emitObject(input))
	event := &descriptorpb.DescriptorProto{Name: proto.String("Event"), Field: []*descriptorpb.FieldDescriptorProto{{
		Name: proto.String("type"), Number: proto.Int32(1),
		Type:  descriptorpb.FieldDescriptorProto_TYPE_STRING.Enum(),
		Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(),
	}}}
	file.MessageType = append(file.MessageType, event)
	return &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{file}}
}

// ---------- facts and lowering ----------

type guardFacts map[string]bool // key -> proven value

func pathKey(path []string) string { return "input." + strings.Join(path, ".") }
func presentKey(path []string) string { return pathKey(path) + "#present" }
func nonNullKey(path []string) string { return pathKey(path) + "#nonnull" }

// selectPath returns the field path of a select chain rooted at the variable.
func selectPath(e ast.Expr) ([]string, bool) {
	if e.Kind() == ast.IdentKind {
		return []string{e.AsIdent()}, true
	}
	if e.Kind() == ast.SelectKind {
		sel := e.AsSelect()
		base, ok := selectPath(sel.Operand())
		if !ok {
			return nil, false
		}
		return append(base, sel.FieldName()), true
	}
	return nil, false
}

func isNullLiteral(e ast.Expr) bool {
	return e.Kind() == ast.LiteralKind && e.AsLiteral().Type().TypeName() == "null_type"
}

// collectFacts returns the facts implied when expr evaluates to truth.
func collectFacts(e ast.Expr, truth bool, facts guardFacts) guardFacts {
	if e.Kind() == ast.SelectKind && e.AsSelect().IsTestOnly() {
		path, ok := selectPath(e)
		if ok && len(path) >= 2 && path[0] == "input" && truth {
			setPrefixFacts(path[1:], facts, true, false)
		}
		return facts
	}
	if e.Kind() == ast.CallKind {
		call := e.AsCall()
		args := call.Args()
		switch call.FunctionName() {
		case "_&&_":
			if truth && len(args) == 2 {
				collectFacts(args[0], true, facts)
				collectFacts(args[1], true, facts)
			}
			return facts
		case "_||_":
			if !truth && len(args) == 2 {
				collectFacts(args[0], false, facts)
				collectFacts(args[1], false, facts)
			}
			return facts
		case "!_":
			if len(args) == 1 {
				collectFacts(args[0], !truth, facts)
			}
			return facts
		case "_!=_", "_==_":
			if len(args) != 2 {
				return facts
			}
			path, ok := selectPath(args[0])
			if !ok || len(path) < 2 || path[0] != "input" {
				return facts
			}
			if !isNullLiteral(args[1]) {
				return facts
			}
			ne := call.FunctionName() == "_!=_"
			// truth of != null proves present+nonNull; truth of == null proves present+null.
			if truth {
				setPrefixFacts(path[1:], facts, true, ne)
			} else {
				setPrefixFacts(path[1:], facts, true, !ne)
			}
			return facts
		case "has":
			if len(args) != 1 {
				return facts
			}
			path, ok := selectPath(args[0])
			if !ok || len(path) < 2 || path[0] != "input" {
				return facts
			}
			if truth {
				setPrefixFacts(path[1:], facts, true, false)
			}
			return facts
		}
	}
	return facts
}

func setPrefixFacts(path []string, facts guardFacts, present, nonNull bool) {
	for i := 1; i <= len(path); i++ {
		prefix := path[:i]
		if present {
			facts[presentKey(prefix)] = true
		}
		if nonNull {
			facts[nonNullKey(prefix)] = true
		}
	}
}

type plan struct {
	valueExpr    string
	presenceExpr string
	nullExpr     string
	nonNullExpr  string
	fullPath     []string
	needPresent  [][]string
	needNonNull  [][]string
	field        *g4Field
}

// planPath builds wire access expressions and the guards a value read needs.
func planPath(root *g4Object, path []string) (*plan, error) {
	cur := root
	p := &plan{}
	expr := "input"
	for index, segment := range path {
		field := cur.field(segment)
		if field == nil {
			return nil, fmt.Errorf("unknown field %q", segment)
		}
		last := index == len(path)-1
		base := expr + "." + segment
		if last {
			p.field = field
			p.fullPath = path
			if field.nullable {
				p.valueExpr = base + ".value"
				p.presenceExpr = "has(" + base + ")"
				p.nullExpr = "has(" + base + ".is_null)"
				p.nonNullExpr = "has(" + base + ".value)"
				p.needNonNull = append(p.needNonNull, path[:index+1])
				if field.optional {
					p.needPresent = append(p.needPresent, path[:index+1])
				}
			} else {
				p.valueExpr = base
				p.presenceExpr = "has(" + base + ")"
				if field.optional {
					p.needPresent = append(p.needPresent, path[:index+1])
				}
			}
			return p, nil
		}
		if field.kind != "object" {
			return nil, fmt.Errorf("field %q is not an object", segment)
		}
		if field.nullable {
			p.needNonNull = append(p.needNonNull, path[:index+1])
			expr = base + ".value"
		} else {
			if field.optional {
				p.needPresent = append(p.needPresent, path[:index+1])
			}
			expr = base
		}
		cur = field.nested
	}
	return nil, fmt.Errorf("empty path")
}

func checkGuards(p *plan, facts guardFacts) error {
	for _, path := range p.needPresent {
		if !facts[presentKey(path)] {
			return fmt.Errorf("missing presence guard for %s", pathKey(path))
		}
	}
	for _, path := range p.needNonNull {
		if !facts[nonNullKey(path)] {
			return fmt.Errorf("missing non-null guard for %s", pathKey(path))
		}
	}
	return nil
}

func checkGuardsExceptSelf(p *plan, facts guardFacts) error {
	self := pathKey(p.fullPath)
	for _, path := range p.needPresent {
		if pathKey(path) == self {
			continue
		}
		if !facts[presentKey(path)] {
			return fmt.Errorf("missing presence guard for %s", pathKey(path))
		}
	}
	for _, path := range p.needNonNull {
		if pathKey(path) == self {
			continue
		}
		if !facts[nonNullKey(path)] {
			return fmt.Errorf("missing non-null guard for %s", pathKey(path))
		}
	}
	return nil
}

func literalText(e ast.Expr) (string, error) {
	if e.Kind() != ast.LiteralKind {
		return "", fmt.Errorf("not a literal")
	}
	lit := e.AsLiteral()
	switch lit.Type().TypeName() {
	case "int":
		return fmt.Sprintf("%d", lit.Value()), nil
	case "double":
		return fmt.Sprintf("%v", lit.Value()), nil
	case "string":
		return fmt.Sprintf("%q", lit.Value()), nil
	case "bool":
		if lit.Value() == true {
			return "true", nil
		}
		return "false", nil
	}
	return "", fmt.Errorf("unsupported literal type %s", lit.Type().TypeName())
}

func fieldCELType(field *g4Field) string {
	if field.nullable {
		return field.kind
	}
	return field.kind
}

func literalMatches(field *g4Field, e ast.Expr) error {
	name := e.AsLiteral().Type().TypeName()
	want := field.kind
	switch want {
	case "int":
		if name != "int" {
			return fmt.Errorf("int field compared with %s", name)
		}
	case "double":
		if name != "double" {
			return fmt.Errorf("double field compared with %s", name)
		}
	case "string":
		if name != "string" {
			return fmt.Errorf("string field compared with %s", name)
		}
	case "bool":
		if name != "bool" {
			return fmt.Errorf("bool field compared with %s", name)
		}
	}
	return nil
}

const (
	wireAnd = "_&&_"
	wireOr  = "_||_"
	wireNot = "!_"
	wireEq  = "_==_"
	wireNe  = "_!=_"
)

func lowerExpr(e ast.Expr, root *g4Object, facts guardFacts) (string, error) {
	switch e.Kind() {
	case ast.LiteralKind:
		return literalText(e)
	case ast.IdentKind:
		return e.AsIdent(), nil
	case ast.SelectKind:
		sel := e.AsSelect()
		path, ok := selectPath(e)
		if !ok || len(path) < 2 || path[0] != "input" {
			return "", fmt.Errorf("unsupported select")
		}
		if sel.IsTestOnly() {
			p, err := planPath(root, path[1:])
			if err != nil {
				return "", err
			}
			return p.presenceExpr, nil
		}
		// A bare value read still needs its guards.
		p, err := planPath(root, path[1:])
		if err != nil {
			return "", err
		}
		if err := checkGuards(p, facts); err != nil {
			return "", err
		}
		return p.valueExpr, nil
	case ast.CallKind:
		call := e.AsCall()
		args := call.Args()
		switch call.FunctionName() {
		case wireAnd, wireOr:
			if len(args) != 2 {
				return "", fmt.Errorf("bad arity")
			}
			left, err := lowerExpr(args[0], root, facts)
			if err != nil {
				return "", err
			}
			branch := guardFacts{}
			for k, v := range facts {
				branch[k] = v
			}
			truth := call.FunctionName() == wireAnd
			collectFacts(args[0], truth, branch)
			right, err := lowerExpr(args[1], root, branch)
			if err != nil {
				return "", err
			}
			symbol := "&&"
			if call.FunctionName() == wireOr {
				symbol = "||"
			}
			return "(" + left + " " + symbol + " " + right + ")", nil
		case wireNot:
			if len(args) != 1 {
				return "", fmt.Errorf("bad arity")
			}
			inner, err := lowerExpr(args[0], root, facts)
			if err != nil {
				return "", err
			}
			return "!" + "(" + inner + ")", nil
		case wireEq, wireNe, "_<_", "_<=_", "_>_", "_>=_":
			return lowerComparison(call.FunctionName(), args, root, facts)
		case "has":
			if len(args) != 1 {
				return "", fmt.Errorf("bad has arity")
			}
			path, ok := selectPath(args[0])
			if !ok || len(path) < 2 || path[0] != "input" {
				return "", fmt.Errorf("has on unsupported expression")
			}
			p, err := planPath(root, path[1:])
			if err != nil {
				return "", err
			}
			return p.presenceExpr, nil
		}
		return "", fmt.Errorf("unsupported function %q", call.FunctionName())
	}
	return "", fmt.Errorf("unsupported expression kind %v", e.Kind())
}

func lowerComparison(fn string, args []ast.Expr, root *g4Object, facts guardFacts) (string, error) {
	if len(args) != 2 {
		return "", fmt.Errorf("bad comparison arity")
	}
	left, right := args[0], args[1]
	if isEventType(left) && right.Kind() == ast.LiteralKind {
		lit, err := literalText(right)
		if err != nil {
			return "", err
		}
		return "(event.type " + fnSymbol(fn) + " " + lit + ")", nil
	}
	if isEventType(right) && left.Kind() == ast.LiteralKind {
		lit, err := literalText(left)
		if err != nil {
			return "", err
		}
		return "(" + lit + " " + fnSymbol(fn) + " event.type)", nil
	}
	if isNullLiteral(right) {
		if fn != wireEq && fn != wireNe {
			return "", fmt.Errorf("null only with == or !=")
		}
		path, ok := selectPath(left)
		if !ok || len(path) < 2 || path[0] != "input" {
			return "", fmt.Errorf("null compared with non-input expression")
		}
		p, err := planPath(root, path[1:])
		if err != nil {
			return "", err
		}
		if !p.field.nullable {
			return "", fmt.Errorf("null comparison on non-nullable %s", pathKey(path[1:]))
		}
		if err := checkGuardsExceptSelf(p, facts); err != nil {
			return "", err
		}
		if fn == wireEq {
			return p.nullExpr, nil
		}
		return p.nonNullExpr, nil
	}
	if isNullLiteral(left) {
		return "", fmt.Errorf("null on the left is not supported")
	}
	// Determine field path and literal side.
	if path, ok := selectPath(left); ok && len(path) >= 2 && path[0] == "input" {
		if right.Kind() != ast.LiteralKind {
			return "", fmt.Errorf("comparison requires a literal")
		}
		p, err := planPath(root, path[1:])
		if err != nil {
			return "", err
		}
		if err := literalMatches(p.field, right); err != nil {
			return "", err
		}
		if err := checkGuards(p, facts); err != nil {
			return "", err
		}
		lit, err := literalText(right)
		if err != nil {
			return "", err
		}
		return "(" + p.valueExpr + " " + fnSymbol(fn) + " " + lit + ")", nil
	}
	if path, ok := selectPath(right); ok && len(path) >= 2 && path[0] == "input" {
		if left.Kind() != ast.LiteralKind {
			return "", fmt.Errorf("comparison requires a literal")
		}
		p, err := planPath(root, path[1:])
		if err != nil {
			return "", err
		}
		if err := literalMatches(p.field, left); err != nil {
			return "", err
		}
		if err := checkGuards(p, facts); err != nil {
			return "", err
		}
		lit, err := literalText(left)
		if err != nil {
			return "", err
		}
		return "(" + lit + " " + fnSymbol(fn) + " " + p.valueExpr + ")", nil
	}
	leftText, err := literalText(left)
	if err != nil {
		return "", err
	}
	rightText, err := literalText(right)
	if err != nil {
		return "", err
	}
	return "(" + leftText + " " + fnSymbol(fn) + " " + rightText + ")", nil
}

func fnSymbol(fn string) string {
	switch fn {
	case wireEq:
		return "=="
	case wireNe:
		return "!="
	case "_<_":
		return "<"
	case "_<=_":
		return "<="
	case "_>_":
		return ">"
	case "_>=_":
		return ">="
	}
	return fn
}

// eventSelectPath reports whether e is event.type.
func isEventType(e ast.Expr) bool {
	path, ok := selectPath(e)
	return ok && len(path) == 2 && path[0] == "event" && path[1] == "type"
}

// ---------- test harness ----------

func ac013Request(t *testing.T) DevelopmentBuildRequest {
	t.Helper()
	request := addDevelopmentSecondSkill(t, loadDevelopmentFixture(t), "  ca-context: urn:example:ca:host-context\n")
	request = replaceDevelopmentSkillFileBytes(t, request,
		"skills/verify-ue-registration/assurance/contract.yaml", []byte(
			"goal: ue.registration_verified\n"+
				"contextSchema: ca-context::urn:example:ca:invocation-context:v1\n"+
				"requestSchema: schemas/request.yaml\n"+
				"dependencies:\n"+
				"  ca-context: urn:example:ca:host-context\n"+
				"  ca: urn:example:ca:tools\n"+
				"  ac: urn:example:ac:input\n"+
				"capabilities:\n"+
				"  - example.registration-read\n"))
	request = replaceDevelopmentSkillFileBytes(t, request,
		"skills/"+developmentSecondSkill+"/assurance/contract.yaml", []byte(
			"goal: ue.context_only\n"+
				"contextSchema: ca-context::urn:example:ca:invocation-context:v1\n"+
				"requestSchema: schemas/request.yaml\n"+
				"dependencies:\n"+
				"  ca-context: urn:example:ca:host-context\n"+
				"  ac2: urn:example:ac2:input\n"))
	request.Files = append(request.Files,
		File{Path: "skills/verify-ue-registration/schemas/request.yaml",
			Bytes: []byte("$schema: https://json-schema.org/draft/2020-12/schema\n$ref: ac::urn:example:ac:input:v1\n")},
		File{Path: "skills/" + developmentSecondSkill + "/schemas/request.yaml",
			Bytes: []byte("$schema: https://json-schema.org/draft/2020-12/schema\n$ref: ac2::urn:example:ac2:input:v1\n")},
	)
	sort.Slice(request.Files, func(i, j int) bool { return request.Files[i].Path < request.Files[j].Path })
	packages := []developmentTestPackage{
		{
			ID: "urn:example:ac:input", Publisher: "example-ac-owner",
			Files: map[string][]byte{"input.schema.yaml": []byte(
				"$schema: https://json-schema.org/draft/2020-12/schema\n" +
					"$id: urn:example:ac:input:v1\n" +
					"type: object\nadditionalProperties: false\n" +
					"required: [count, ratio, wrapped, nested]\n" +
					"properties:\n" +
					"  count:\n    type: integer\n" +
					"  ratio:\n    type: number\n" +
					"  note:\n    type: string\n" +
					"  wrapped:\n    type: [integer, \"null\"]\n" +
					"  both:\n    type: [string, \"null\"]\n" +
					"  nested:\n" +
					"    type: object\n    additionalProperties: false\n    required: [inner]\n" +
					"    properties:\n      inner:\n        type: string\n")},
			Exports: []map[string]any{{"kind": "Schema", "id": "urn:example:ac:input:v1", "path": "input.schema.yaml"}},
			Deps:    map[string]string{},
		},
		{
			ID: "urn:example:ac2:input", Publisher: "example-ac2-owner",
			Files: map[string][]byte{"input.schema.yaml": []byte(
				"$schema: https://json-schema.org/draft/2020-12/schema\n" +
					"$id: urn:example:ac2:input:v1\n" +
					"type: object\nadditionalProperties: false\n" +
					"required: [token]\n" +
					"properties:\n  token:\n    type: string\n")},
			Exports: []map[string]any{{"kind": "Schema", "id": "urn:example:ac2:input:v1", "path": "input.schema.yaml"}},
			Deps:    map[string]string{},
		},
	}
	request = addDevelopmentTestGraph(t, request, packages, map[string]string{
		"ac": "urn:example:ac:input", "ac2": "urn:example:ac2:input",
	})
	return request
}

func ac013Registry(t *testing.T, request DevelopmentBuildRequest) (BuildRequest, *developmentSemantics, map[string]*g4Object) {
	t.Helper()
	env, diagnostics := validateDevelopmentRequest(request)
	if len(diagnostics) > 0 {
		t.Fatalf("validateDevelopmentRequest: %#v", diagnostics)
	}
	scope, scopeDiagnostics := buildDevelopmentLinkScope(env)
	if len(scopeDiagnostics) > 0 {
		t.Fatalf("buildDevelopmentLinkScope: %#v", scopeDiagnostics)
	}
	legacy, synthetic := env.legacyRequest()
	semantics := newDevelopmentSemantics(env, scope, synthetic, newDevelopmentRequirementCollector())
	legacy.development = semantics
	if diagnostics := checkSourcesWithDevelopment(legacy, semantics); hasErrorDiagnostic(diagnostics) {
		t.Fatalf("checkSourcesWithDevelopment: %#v", diagnostics)
	}
	roots := map[string]*g4Object{}
	for _, name := range legacy.Targets {
		skill := wp3aParseSkillAST(t, legacy, name)
		identity := validateDependencyIdentity(legacy, skill)
		registry := buildSchemaRegistry(legacy, skill, identity, legacy.development)
		ref := scalar(skill.Contract.RequestSchema)
		if ref == "" {
			t.Fatalf("%s has no requestSchema", name)
		}
		resource, ok := registry.local["skills/"+name+"/"+ref]
		if !ok {
			t.Fatalf("%s requestSchema %q not found", name, ref)
		}
		effective, problem := registry.resolveSchemaRoot(resource)
		if problem != "" {
			t.Fatalf("%s resolveSchemaRoot: %s", name, problem)
		}
		root, err := parseG4Object(registry, effective, "Input", 0)
		if err != nil {
			t.Fatalf("%s parse schema: %v", name, err)
		}
		roots[name] = root
	}
	return legacy, semantics, roots
}

type skillWire struct {
	set    *descriptorpb.FileDescriptorSet
	env    *cel.Env
	input  protoreflect.MessageDescriptor
	event  protoreflect.MessageDescriptor
	byExpr map[string]*cel.Ast
}

type ac013Case struct {
	ID     string         `json:"id"`
	Skill  string         `json:"skill"`
	Expr   string         `json:"expr"`
	Kind   string         `json:"eventKind,omitempty"`
	Input  map[string]any `json:"input"`
	Want   string         `json:"want"`
	Wire   string         `json:"wire,omitempty"`
	Actual string         `json:"actual,omitempty"`
	Note   string         `json:"note,omitempty"`
}

func TestAC013PocGenerate(t *testing.T) {
	out := os.Getenv("AC013_OUT")
	if out == "" {
		t.Skip("AC013_OUT not set")
	}
	request := ac013Request(t)
	legacy, _, roots := ac013Registry(t, request)
	_ = legacy

	wires := map[string]*skillWire{}

	for name, root := range roots {
		pkg := "ac013a"
		if name == developmentSecondSkill {
			pkg = "ac013b"
		}
		builder := &descBuilder{pkg: pkg}
		set := builder.build(root)
		desc, err := protodesc.NewFile(set.File[0], nil)
		if err != nil {
			t.Fatalf("%s protodesc: %v", name, err)
		}
		env, err := cel.NewEnv(
			cel.TypeDescs(set),
			cel.Variable("input", cel.ObjectType(pkg+".Input")),
			cel.Variable("event", cel.ObjectType(pkg+".Event")),
		)
		if err != nil {
			t.Fatalf("%s env: %v", name, err)
		}
		wires[name] = &skillWire{
			set:    set,
			env:    env,
			input:  desc.Messages().ByName("Input"),
			event:  desc.Messages().ByName("Event"),
			byExpr: map[string]*cel.Ast{},
		}
	}

	// Author expression -> wire expression, with static rejection checks.
	valid := []ac013Case{
		{ID: "true", Skill: "verify-ue-registration", Expr: `event.type == "create" && input.count == 1`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "false", Skill: "verify-ue-registration", Expr: `event.type == "create" && input.count == 1`, Kind: "modify", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "false"},
		{ID: "missing_kind", Skill: "verify-ue-registration", Expr: `event.type == "create" && input.count == 1`, Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "error"},
		{ID: "missing_optional", Skill: "verify-ue-registration", Expr: `has(input.note) && input.note == "x"`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "false"},
		{ID: "present_optional", Skill: "verify-ue-registration", Expr: `has(input.note) && input.note == "x"`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "note": "x", "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "nullable_value", Skill: "verify-ue-registration", Expr: `input.wrapped != null && input.wrapped == 5`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "nullable_null", Skill: "verify-ue-registration", Expr: `input.wrapped != null && input.wrapped == 5`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"is_null": true}, "nested": map[string]any{"inner": "y"}}, Want: "false"},
		{ID: "nullable_eq_null", Skill: "verify-ue-registration", Expr: `has(input.both) && input.both == null`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "both": map[string]any{"is_null": true}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "both_absent", Skill: "verify-ue-registration", Expr: `has(input.both) && input.both == null`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "false"},
		{ID: "both_value", Skill: "verify-ue-registration", Expr: `has(input.both) && input.both != null && input.both == "ok"`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "both": map[string]any{"value": "ok"}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "nested", Skill: "verify-ue-registration", Expr: `has(input.nested.inner) && input.nested.inner == "y"`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "int64_max", Skill: "verify-ue-registration", Expr: `input.count == 9223372036854775807`, Kind: "create", Input: map[string]any{"count": int64(9223372036854775807), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "double", Skill: "verify-ue-registration", Expr: `input.ratio == 2.5`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "double_max", Skill: "verify-ue-registration", Expr: `input.ratio == 1.7976931348623157e308`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 1.7976931348623157e308, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "and_chain", Skill: "verify-ue-registration", Expr: `event.type == "create" && input.count == 1 && input.ratio == 2.5`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "or_guarded", Skill: "verify-ue-registration", Expr: `!has(input.note) || input.note == "x"`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "not", Skill: "verify-ue-registration", Expr: `!(input.count == 2)`, Kind: "create", Input: map[string]any{"count": int64(1), "ratio": 2.5, "wrapped": map[string]any{"value": int64(5)}, "nested": map[string]any{"inner": "y"}}, Want: "true"},
		{ID: "second_skill", Skill: developmentSecondSkill, Expr: `event.type == "create" && input.token == "t"`, Kind: "create", Input: map[string]any{"token": "t"}, Want: "true"},
	}
	reject := []struct {
		ID    string
		Skill string
		Expr  string
	}{
		{"unknown_field", "verify-ue-registration", `input.unknown == 1`},
		{"unguarded_optional", "verify-ue-registration", `input.note == "x"`},
		{"unguarded_nullable", "verify-ue-registration", `input.wrapped == 5`},
		{"int_double_mix", "verify-ue-registration", `input.count == 1.0`},
		{"unsafe_or", "verify-ue-registration", `has(input.note) || input.note == "x"`},
		{"cross_skill", "verify-ue-registration", `input.token == "t"`},
	}

	// Static rejections.
	for _, rc := range reject {
		wire, err := lowerAuthor(wires[rc.Skill], roots[rc.Skill], rc.Expr)
		if err == nil {
			t.Errorf("%s: expected static rejection, got wire %q", rc.ID, wire)
		} else {
			t.Logf("rejected %s: %v", rc.ID, err)
		}
	}

	// Valid cases: lower, compile, evaluate in Go.
	for index := range valid {
		c := &valid[index]
		w := wires[c.Skill]
		wire, err := lowerAuthor(w, roots[c.Skill], c.Expr)
		if err != nil {
			t.Fatalf("%s: lower %q: %v", c.ID, c.Expr, err)
		}
		c.Wire = wire
		program, err := w.env.Program(mustCompile(t, w.env, wire))
		if err != nil {
			t.Fatalf("%s: program: %v", c.ID, err)
		}
		c.Actual = evalGo(program, w, c.Kind, c.Input)
		if c.Actual != c.Want {
			t.Fatalf("%s: go actual=%s want=%s wire=%s", c.ID, c.Actual, c.Want, wire)
		}
		t.Logf("%s: wire=%s go=%s", c.ID, wire, c.Actual)
	}

	// Emit artifacts: one checked/type pair per Skill per expression.
	if err := os.MkdirAll(out, 0o755); err != nil {
		t.Fatal(err)
	}
	for name, w := range wires {
		for _, c := range valid {
			if c.Skill != name {
				continue
			}
			expr := mustCompile(t, w.env, c.Wire)
			checked := mustChecked(expr)
			anyMsg := &anypb.Any{}
			if err := anypb.MarshalFrom(anyMsg, checked, proto.MarshalOptions{Deterministic: true}); err != nil {
				t.Fatal(err)
			}
			payload := anyMsg
			prefix := name + "-" + c.ID
			if err := os.WriteFile(filepath.Join(out, prefix+".checked.pb"), mustProto(payload), 0o644); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(out, prefix+".types.pb"), mustProto(w.set), 0o644); err != nil {
				t.Fatal(err)
			}
		}
	}
	raw, err := json.MarshalIndent(struct {
		Source  string       `json:"source"`
		Version string       `json:"version"`
		Cases   []ac013Case  `json:"cases"`
	}{Source: "ca-skill-compiler@255ab85", Version: "ac013-poc-1", Cases: valid}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "cases.json"), raw, 0o644); err != nil {
		t.Fatal(err)
	}
}

func lowerAuthor(w *skillWire, root *g4Object, source string) (string, error) {
	parsed, issues := w.env.Parse(source)
	if issues != nil && issues.Err() != nil {
		return "", issues.Err()
	}
	return lowerExpr(parsed.NativeRep().Expr(), root, guardFacts{})
}

func mustCompile(t *testing.T, env *cel.Env, source string) *cel.Ast {
	t.Helper()
	checked, issues := env.Compile(source)
	if issues != nil && issues.Err() != nil {
		t.Fatalf("compile %q: %v", source, issues.Err())
	}
	return checked
}

func mustChecked(expr *cel.Ast) *celpb.CheckedExpr {
	legacy, err := cel.AstToCheckedExpr(expr)
	if err != nil {
		panic(err)
	}
	portable := &celpb.CheckedExpr{}
	if err := proto.Unmarshal(mustProto(legacy), portable); err != nil {
		panic(err)
	}
	return portable
}

func mustProto(msg proto.Message) []byte {
	out, err := proto.MarshalOptions{Deterministic: true}.Marshal(msg)
	if err != nil {
		panic(err)
	}
	return out
}

func evalGo(program cel.Program, w *skillWire, kind string, spec map[string]any) string {
	activation := map[string]any{"input": buildDynamic(w.input, spec)}
	if kind != "" {
		activation["event"] = buildDynamic(w.event, map[string]any{"type": kind})
	}
	out, _, err := program.Eval(activation)
	if err != nil {
		return "error"
	}
	if out == nil {
		return "error"
	}
	switch value := out.Value().(type) {
	case bool:
		if value {
			return "true"
		}
		return "false"
	}
	return "error"
}

func buildDynamic(md protoreflect.MessageDescriptor, spec map[string]any) *dynamicpb.Message {
	msg := dynamicpb.NewMessage(md)
	for name, raw := range spec {
		fd := md.Fields().ByName(protoreflect.Name(name))
		if fd == nil {
			panic("unknown field in case input: " + name)
		}
		switch typed := raw.(type) {
		case map[string]any:
			msg.Set(fd, protoreflect.ValueOfMessage(buildDynamic(fd.Message(), typed)))
		case string:
			msg.Set(fd, protoreflect.ValueOfString(typed))
		case bool:
			msg.Set(fd, protoreflect.ValueOfBool(typed))
		case int64:
			msg.Set(fd, protoreflect.ValueOfInt64(typed))
		case int:
			msg.Set(fd, protoreflect.ValueOfInt64(int64(typed)))
		case float64:
			msg.Set(fd, protoreflect.ValueOfFloat64(typed))
		default:
			panic(fmt.Sprintf("unsupported input value type %T for %s", raw, name))
		}
	}
	return msg
}





