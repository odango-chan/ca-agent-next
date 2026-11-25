package main

import (
	"cel.dev/cel-go/cel"
	"cel.dev/cel-go/common/ast"
	celpb "cel.dev/expr"
	"fmt"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protodesc"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
	"google.golang.org/protobuf/types/known/anypb"
	"os"
	"path/filepath"
)

func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}

type facts struct{ present, nonNull bool }

func countField(e ast.Expr) bool {
	if e.Kind() != ast.SelectKind {
		return false
	}
	field := e.AsSelect()
	target := field.Operand()
	return field.FieldName() == "count" && target.Kind() == ast.IdentKind && target.AsIdent() == "input"
}
func isPresence(e ast.Expr) bool { return countField(e) && e.AsSelect().IsTestOnly() }
func isNull(e ast.Expr) bool {
	return e.Kind() == ast.LiteralKind && fmt.Sprint(e.AsLiteral()) == "0" && e.AsLiteral().Type().TypeName() == "null_type"
}
func lower(e ast.Expr, known facts) (string, facts, error) {
	if isPresence(e) {
		known.present = true
		return "has(input.count)", known, nil
	}
	if e.Kind() != ast.CallKind {
		return "", known, fmt.Errorf("unsupported expression kind %v", e.Kind())
	}
	c := e.AsCall()
	args := c.Args()
	if len(args) != 2 {
		return "", known, fmt.Errorf("unsupported arity")
	}
	left, right := args[0], args[1]
	switch c.FunctionName() {
	case "_&&_":
		l, after, err := lower(left, known)
		if err != nil {
			return "", known, err
		}
		r, done, err := lower(right, after)
		return "(" + l + " && " + r + ")", done, err
	case "_==_", "_!=_":
		if countField(left) && isNull(right) {
			if !known.present {
				return "", known, fmt.Errorf("missing presence guard before null comparison")
			}
			if c.FunctionName() == "_!=_" {
				known.nonNull = true
				return "has(input.count.count)", known, nil
			}
			return "has(input.count.is_null)", known, nil
		}
		if countField(left) && right.Kind() == ast.LiteralKind {
			if !known.present || !known.nonNull {
				return "", known, fmt.Errorf("scalar read without presence/non-null guard")
			}
			if right.AsLiteral().Type().TypeName() != "int" || c.FunctionName() != "_==_" {
				return "", known, fmt.Errorf("unsupported scalar comparison")
			}
			return fmt.Sprintf("input.count.count == %v", right.AsLiteral()), known, nil
		}
		if left.Kind() == ast.IdentKind && left.AsIdent() == "kind" && right.Kind() == ast.LiteralKind && right.AsLiteral().Type().TypeName() == "string" && c.FunctionName() == "_==_" {
			return fmt.Sprintf("kind == %q", right.AsLiteral().Value()), known, nil
		}
	}
	return "", known, fmt.Errorf("unsupported author expression")
}
func lowerSource(env *cel.Env, source string) (string, error) {
	parsed, issues := env.Parse(source)
	if issues.Err() != nil {
		return "", issues.Err()
	}
	wire, _, err := lower(parsed.NativeRep().Expr(), facts{})
	return wire, err
}
func main() {
	field := &descriptorpb.FieldDescriptorProto{Name: proto.String("count"), Number: proto.Int32(1), Type: descriptorpb.FieldDescriptorProto_TYPE_INT64.Enum(), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum()}
	field.OneofIndex = proto.Int32(0)
	nullField := &descriptorpb.FieldDescriptorProto{Name: proto.String("is_null"), Number: proto.Int32(2), Type: descriptorpb.FieldDescriptorProto_TYPE_BOOL.Enum(), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum(), OneofIndex: proto.Int32(0)}
	wrappedField := &descriptorpb.FieldDescriptorProto{Name: proto.String("count"), Number: proto.Int32(1), Type: descriptorpb.FieldDescriptorProto_TYPE_MESSAGE.Enum(), TypeName: proto.String(".ac013.NullableInt"), Label: descriptorpb.FieldDescriptorProto_LABEL_OPTIONAL.Enum()}
	file := &descriptorpb.FileDescriptorProto{Name: proto.String("ac013.proto"), Package: proto.String("ac013"), Syntax: proto.String("proto2"), MessageType: []*descriptorpb.DescriptorProto{{Name: proto.String("Input"), Field: []*descriptorpb.FieldDescriptorProto{wrappedField}}, {Name: proto.String("Other")}, {Name: proto.String("NullableInt"), OneofDecl: []*descriptorpb.OneofDescriptorProto{{Name: proto.String("state")}}, Field: []*descriptorpb.FieldDescriptorProto{field, nullField}}}}
	set := &descriptorpb.FileDescriptorSet{File: []*descriptorpb.FileDescriptorProto{file}}
	desc := must(protodesc.NewFile(file, nil))
	input := desc.Messages().ByName("Input")
	env := must(cel.NewEnv(cel.TypeDescs(set), cel.Variable("input", cel.ObjectType("ac013.Input")), cel.Variable("kind", cel.StringType)))
	if _, original := env.Compile("has(input.count) && input.count != null && input.count == 1"); original.Err() != nil {
		fmt.Println("original author expression on wire type:", original.Err())
	} else {
		panic("expected wrapper to need explicit author-to-wire translation")
	}
 source := "kind == \"create\" && has(input.count) && input.count != null && input.count == 9223372036854775807"
 wire := must(lowerSource(env,source))
 fmt.Println("translated:",wire)
 for _, unmatched := range []string{"input.count != null && input.count == 1","has(input.count) && input.count == 1","has(input.count) || input.count == 1","has(input.count) && input.count != null && input.count == 1.0"} {
  if _, err := lowerSource(env,unmatched); err == nil { panic("accepted invalid source: "+unmatched) } else { fmt.Println("rejected:",err) }
 }
 fmt.Println("null comparison:",must(lowerSource(env,"has(input.count) && input.count == null")))
 expr, issues := env.Compile(wire)
	if issues.Err() != nil {
		panic(issues.Err())
	}
	if _, bad := env.Compile("input.unknown == 1"); bad.Err() == nil {
		panic("unknown field accepted")
	}
	other := must(cel.NewEnv(cel.TypeDescs(set), cel.Variable("input", cel.ObjectType("ac013.Other"))))
	if _, bad := other.Compile("input.count == 1"); bad.Err() == nil {
		panic("foreign schema field accepted")
	}
	checked := must(cel.AstToCheckedExpr(expr))
	portable := &celpb.CheckedExpr{}
	if err := proto.Unmarshal(must(proto.Marshal(checked)), portable); err != nil {
		panic(err)
	}
	for name, msg := range map[string]proto.Message{"lowered.checked.pb": must(anypb.New(portable)), "lowered.types.pb": set} {
		if err := os.WriteFile(filepath.Join(os.Args[1], name), must(proto.Marshal(msg)), 0600); err != nil {
			panic(err)
		}
	}
	prog := must(env.Program(expr))
	present := dynamicpb.NewMessage(input)
	count := input.Fields().ByName("count")
	countValue := dynamicpb.NewMessage(count.Message())
	countValue.Set(count.Message().Fields().ByName("count"), protoreflect.ValueOfInt64(9223372036854775807))
	present.Set(count, protoreflect.ValueOfMessage(countValue))
	null := dynamicpb.NewMessage(input)
	nullValue := dynamicpb.NewMessage(count.Message())
	nullValue.Set(count.Message().Fields().ByName("is_null"), protoreflect.ValueOfBool(true))
	null.Set(count, protoreflect.ValueOfMessage(nullValue))
	if !null.Has(count) || nullValue.Has(count.Message().Fields().ByName("count")) {
		panic("invalid null state")
	}
	for _, test := range []struct {
		kind  string
		input *dynamicpb.Message
		want  string
	}{{"create", present, "true"}, {"modify", present, "false"}, {"create", dynamicpb.NewMessage(input), "false"}, {"create", null, "false"}} {
		result, _, err := prog.Eval(map[string]any{"kind": test.kind, "input": test.input})
		if err != nil || fmt.Sprint(result) != test.want {
			panic(fmt.Sprintf("Go result=%v error=%v want=%s", result, err, test.want))
		}
		fmt.Println("go", test.kind, test.input.Has(input.Fields().ByName("count")), result)
	}
	if _, _, err := prog.Eval(map[string]any{"input": present}); err == nil {
		panic("missing kind accepted")
	}
	fmt.Println("go missing kind: error")
}

