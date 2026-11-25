package compiler

// AC-013-01 determinism probe.
//
// It marshals the same cel.expr.CheckedExpr (which carries reference_map and
// type_map) many times in one process and counts distinct byte outputs for the
// default marshaler versus the deterministic one. It also exercises the Any
// payload produced by anypb.MarshalFrom.

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"testing"

	"cel.dev/cel-go/cel"
	celpb "cel.dev/expr"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/anypb"
)

func TestAC013DeterminismProbe(t *testing.T) {
	env, err := cel.NewEnv(cel.Variable("x", cel.IntType), cel.Variable("y", cel.DoubleType))
	if err != nil {
		t.Fatal(err)
	}
	// Each declared variable and ident creates reference_map and type_map entries.
	ast, issues := env.Compile(`x == 1 && y == 2.5`)
	if issues != nil && issues.Err() != nil {
		t.Fatal(issues.Err())
	}
	legacy, err := cel.AstToCheckedExpr(ast)
	if err != nil {
		t.Fatal(err)
	}
	portable := &celpb.CheckedExpr{}
	if err := proto.Unmarshal(mustProto(legacy), portable); err != nil {
		t.Fatal(err)
	}
	fmt.Printf("checked_expr: reference_map=%d type_map=%d\n", len(portable.GetReferenceMap()), len(portable.GetTypeMap()))

	const iterations = 200
	defaultHashes := map[string]bool{}
	deterministicHashes := map[string]bool{}
	anyDefault := map[string]bool{}
	anyDeterministic := map[string]bool{}

	for i := 0; i < iterations; i++ {
		rawDefault, err := proto.Marshal(portable)
		if err != nil {
			t.Fatal(err)
		}
		defaultHashes[hashBytes(rawDefault)] = true

		rawDeterministic, err := proto.MarshalOptions{Deterministic: true}.Marshal(portable)
		if err != nil {
			t.Fatal(err)
		}
		deterministicHashes[hashBytes(rawDeterministic)] = true

		defaultAny, err := anypb.New(portable)
		if err != nil {
			t.Fatal(err)
		}
		anyDefault[hashBytes(mustProto(defaultAny))] = true

		deterministicAny := &anypb.Any{}
		if err := anypb.MarshalFrom(deterministicAny, portable, proto.MarshalOptions{Deterministic: true}); err != nil {
			t.Fatal(err)
		}
		anyDeterministic[hashBytes(mustProto(deterministicAny))] = true
	}

	fmt.Printf("iterations=%d\n", iterations)
	fmt.Printf("default_marshal_distinct=%d\n", len(defaultHashes))
	fmt.Printf("deterministic_marshal_distinct=%d\n", len(deterministicHashes))
	fmt.Printf("anypb_new_distinct=%d\n", len(anyDefault))
	fmt.Printf("anypb_marshalfrom_deterministic_distinct=%d\n", len(anyDeterministic))
	if len(defaultHashes) < 2 {
		t.Log("default marshal happened to be stable in this process; see two-directory run comparison")
	}
	if len(deterministicHashes) != 1 {
		t.Fatalf("deterministic marshal produced %d distinct outputs", len(deterministicHashes))
	}
	if len(anyDeterministic) != 1 {
		t.Fatalf("deterministic Any produced %d distinct outputs", len(anyDeterministic))
	}
}

func hashBytes(raw []byte) string {
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

