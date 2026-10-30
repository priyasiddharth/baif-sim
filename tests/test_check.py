#!/usr/bin/env python3
"""Unit tests for the classification logic in tools/check.py.

These need no toolchain: they exercise the pure functions that turn stage
diagnostics, generated-Lean text and `#print axioms` output into verdicts.
The end-to-end verdicts per fixture are pinned by tests/expected.json
(tests/run_expected.py); this file pins *why* each verdict is produced.

  python3 -m unittest discover -s tests -p 'test_*.py'
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check  # noqa: E402

# The generated Lean of a recorded attempt, committed with the attempt: three
# raw-pointer axioms and one translated function.
SWAP_LEAN = ROOT / "mbpp/aeneas_pristine/mbpp_591_swap_List/attempt-1/lean/Mbpp591SwapList.lean"
SQUARE_LEAN = ROOT / "mbpp/aeneas_pristine/mbpp_8_square_nums/attempt-1/lean/Mbpp8SquareNums.lean"


class Verdicts(unittest.TestCase):
    def test_exit_codes_are_distinct_and_cover_severity(self):
        codes = check.EXIT_CODES
        self.assertEqual(len(set(codes.values())), len(codes))
        self.assertEqual(codes["translates"], 0)
        for v in check.SEVERITY:
            self.assertIn(v, codes)

    def test_severity_order(self):
        # Most severe first; missing_model is the mildest problem.
        self.assertEqual(check.SEVERITY,
                         ["toolchain_problem", "invalid_rust", "unsupported_code", "missing_context", "missing_model"])

    def test_verdict_of_picks_most_severe(self):
        self.assertEqual(check.verdict_of([]), "translates")
        self.assertEqual(check.verdict_of([("missing_model", "a")]), "missing_model")
        self.assertEqual(check.verdict_of([("missing_model", "a"), ("missing_context", "b")]), "missing_context")
        self.assertEqual(check.verdict_of([("missing_model", "a"), ("unsupported_code", "b")]), "unsupported_code")
        self.assertEqual(check.verdict_of([("unsupported_code", "a"), ("toolchain_problem", "b")]), "toolchain_problem")


class LocalFunctions(unittest.TestCase):
    def decl(self, name, local=True):
        return {"item_meta": {"name": name, "is_local": local, "span": {"span": {"beg": {"line": 1, "col": 0}}}}, "body": None}

    def test_drop_glue_is_skipped(self):
        user = [{"Ident": ["crate", 0]}, {"Ident": ["add", 0]}]
        glue = [{"Ident": ["crate", 0]}, {"Ident": ["Arena", 0]}, {"Impl": {"Trait": 8}}, {"Builtin": ["DropGlue", 0]}]
        foreign = [{"Ident": ["core", 0]}, {"Ident": ["mem", 0]}, {"Ident": ["swap", 0]}]
        data = {"translated": {"fun_decls": [self.decl(user), self.decl(glue), self.decl(foreign, local=False), None]}}
        self.assertEqual([f["rust"] for f in check.local_functions(data)], ["crate::add"])

    def test_builtin_segment_is_rendered(self):
        glue = [{"Ident": ["crate", 0]}, {"Ident": ["Arena", 0]}, {"Impl": {"Trait": 8}}, {"Builtin": ["DropGlue", 0]}]
        self.assertEqual(check.name_to_str(glue), "crate::Arena::{impl}::{DropGlue}")
        self.assertTrue(check.is_compiler_generated(glue))


class CharonStage(unittest.TestCase):
    def stage(self, compiled, errors=(), warnings=(), status="ok"):
        return {"rust_compiled": compiled, "errors": list(errors), "warnings": list(warnings), "status": status}

    def test_unresolved_name_is_missing_context(self):
        for code in sorted(check.MISSING_CONTEXT_CODES):
            r = check.classify_charon(self.stage(False, [{"code": code, "message": "cannot find"}]))
            self.assertEqual([v for v, _ in r], ["missing_context"], code)

    def test_other_rustc_error_is_invalid_rust(self):
        r = check.classify_charon(self.stage(False, [{"code": "E0308", "message": "mismatched types"}]))
        self.assertEqual([v for v, _ in r], ["invalid_rust"])

    def test_charon_panic_is_toolchain_problem(self):
        r = check.classify_charon(self.stage(True, [{"code": "panic", "message": "Thread panicked"}], status="failed"))
        self.assertEqual([v for v, _ in r], ["toolchain_problem"])

    def test_include_or_opaque_message_is_missing_context(self):
        r = check.classify_charon(self.stage(True, [{"message": "item is opaque; use --include"}]))
        self.assertEqual([v for v, _ in r], ["missing_context"])

    def test_other_charon_message_is_unsupported(self):
        r = check.classify_charon(self.stage(True, warnings=[{"message": "unsupported: inline asm"}]))
        self.assertEqual([v for v, _ in r], ["unsupported_code"])

    def test_failed_without_diagnostic_is_toolchain_problem(self):
        r = check.classify_charon(self.stage(True, status="failed"))
        self.assertEqual([v for v, _ in r], ["toolchain_problem"])


class AeneasStage(unittest.TestCase):
    def stage(self, errors, status="ok"):
        return {"errors": errors, "warnings": [], "status": status}

    def test_limitation_is_unsupported(self):
        r = check.classify_aeneas(self.stage([{"message": "Breaks to outer loops are not supported yet", "span": None}]), False)
        self.assertEqual([v for v, _ in r], ["unsupported_code"])

    def test_internal_error_is_toolchain_unless_charon_was_broken(self):
        e = [{"message": "Internal error: please file an issue"}]
        self.assertEqual([v for v, _ in check.classify_aeneas(self.stage(e), False)], ["toolchain_problem"])
        self.assertEqual(check.classify_aeneas(self.stage(e), True), [])

    def test_crash_after_limitation_is_its_consequence(self):
        e = [{"message": "not supported", "span": None}, {"message": "Fatal", "crash": True}]
        self.assertEqual([v for v, _ in check.classify_aeneas(self.stage(e), False)],
                         ["unsupported_code", "unsupported_code"])
        self.assertEqual([v for v, _ in check.classify_aeneas(self.stage(e[1:]), False)], ["toolchain_problem"])

    def test_no_lean_file_and_no_diagnostic_is_toolchain_problem(self):
        self.assertEqual([v for v, _ in check.classify_aeneas(self.stage([], "failed"), False)], ["toolchain_problem"])


class LeanErrors(unittest.TestCase):
    def test_missing_field_of_library_trait_structure_is_unsupported(self):
        for crate in ("core", "alloc", "std"):
            v, msg = check.classify_lean_error(f"`any` is not a field of structure `{crate}.iter.traits.iterator.Iterator`")
            self.assertEqual(v, "unsupported_code", crate)
            self.assertIn("library trait structure lacks the method", msg)

    def test_missing_field_of_other_structure_is_missing_model(self):
        v, _ = check.classify_lean_error("`foo` is not a field of structure `Mbpp.MyTrait`")
        self.assertEqual(v, "missing_model")

    def test_unknown_constant_is_missing_model(self):
        self.assertEqual(check.classify_lean_error("unknown constant 'alloc.vec.Vec.sort'")[0], "missing_model")
        self.assertEqual(check.classify_lean_error("unknown identifier 'x'")[0], "missing_model")

    def test_anything_else_is_toolchain_problem(self):
        v, msg = check.classify_lean_error("type mismatch\n  b\nhas type Prop but is expected to have type Bool")
        self.assertEqual(v, "toolchain_problem")
        self.assertIn("does not type-check", msg)


class Axioms(unittest.TestCase):
    def test_origin_by_crate(self):
        self.assertEqual(check.axiom_origin("core::ptr::swap", "my_crate"), "stdlib")
        self.assertEqual(check.axiom_origin("alloc::vec::{alloc::vec::Vec<T>}::truncate", "my_crate"), "stdlib")
        self.assertEqual(check.axiom_origin("std::io::stdin", "my_crate"), "stdlib")
        self.assertEqual(check.axiom_origin("my_crate::helper", "my_crate"), "local")
        self.assertEqual(check.axiom_origin("serde::de::Deserialize", "my_crate"), "dependency")
        self.assertEqual(check.axiom_origin(None, "my_crate"), "library")

    def test_raw_pointer_signature_gets_note(self):
        decl = {"rust": "core::ptr::swap", "text": " {T : Type _} : MutRawPtr T → MutRawPtr T → Result Unit"}
        a = check.axiom_entry("X.core.ptr.swap", decl, "x")
        self.assertEqual(a["origin"], "stdlib")
        self.assertEqual(a["note"], check.RAW_PTR_NOTE)
        decl = {"rust": "core::ptr::read", "text": " {T : Type _} : ConstRawPtr T → Result T"}
        self.assertIn("note", check.axiom_entry("X.core.ptr.read", decl, "x"))

    def test_plain_signature_gets_no_note(self):
        decl = {"rust": "alloc::vec::{alloc::vec::Vec<T>}::truncate",
                "text": " {T : Type _} : alloc.vec.Vec T → Std.Usize → Result (alloc.vec.Vec T)"}
        self.assertNotIn("note", check.axiom_entry("X.alloc.vec.Vec.truncate", decl, "x"))
        # Library axioms have no declaration in the file and never a note.
        self.assertNotIn("note", check.axiom_entry("Lean.ofReduceBool", None, "x"))

    def test_collect_skips_standard_axioms_and_keeps_unused_declared_ones(self):
        decls = {"X.a": {"rust": "core::a", "text": ""}, "X.b": {"rust": "core::b", "text": ""}}
        used = {"X.f": ["propext", "Classical.choice", "Quot.sound", "sorryAx", "X.a", "Lean.ofReduceBool"]}
        got = {a["lean"]: a for a in check.collect_axioms(used, decls, "x")}
        self.assertEqual(set(got), {"X.a", "X.b", "Lean.ofReduceBool"})
        self.assertEqual(got["X.a"]["used_by"], ["X.f"])
        self.assertEqual(got["X.b"]["used_by"], [])          # declared, used by nothing checked: still a hole
        self.assertEqual(got["Lean.ofReduceBool"]["origin"], "library")

    def test_axiom_reason_is_missing_model_and_mentions_note(self):
        a = {"lean": "X.s", "rust": "core::ptr::swap", "origin": "stdlib", "used_by": [], "note": check.RAW_PTR_NOTE}
        v, msg = check.axiom_reason(a)
        self.assertEqual(v, "missing_model")
        self.assertIn("core::ptr::swap", msg)
        self.assertIn(check.RAW_PTR_NOTE, msg)
        v, msg = check.axiom_reason({"lean": "Lean.ofReduceBool", "rust": None, "origin": "library", "used_by": []})
        self.assertEqual((v, msg), ("missing_model", "axiom from the Aeneas Lean library: Lean.ofReduceBool"))


class DocHeaderParsing(unittest.TestCase):
    """DOC_HEADER on the header shapes Aeneas emits."""

    def parse(self, text):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False) as f:
            f.write(text)
        return check.lean_decls(Path(f.name))

    def test_name_with_brackets_and_loop_headers(self):
        text = (
            "/-- [core::slice::{[T]}::as_ptr]:\n    Source: '/rustc/x.rs', lines 1:0-2:1\n"
            "    Name pattern: [core::slice::{[@T]}::as_ptr] -/\n"
            "@[rust_fun \"core::slice::{[@T]}::as_ptr\"]\n"
            "axiom core.slice.Slice.as_ptr {T : Type _} : Slice T → Result (ConstRawPtr T)\n\n"
            "/-- [crate::f]: loop body 0:\n    Source: 'crate.rs', lines 5:4-9:5 -/\n"
            "@[rust_loop_body]\ndef f_loop_body (i : Usize) : Result Usize := ok i\n\n"
            "/-- [crate::f]: loop 0:\n    Source: 'crate.rs', lines 5:4-9:5 -/\n"
            "def f_loop (i : Usize) : Result Usize := f_loop_body i\n\n"
            "/-- [crate::f]\n    Source: 'crate.rs', lines 3:0-10:1 -/\n"
            "def f : Result Usize := sorry\n"
        )
        decls = self.parse(text)
        self.assertEqual([d["rust"] for d in decls], ["core::slice::{[T]}::as_ptr", "crate::f", "crate::f", "crate::f"])
        self.assertEqual([d["kind"] for d in decls], ["axiom", "def", "def", "def"])
        self.assertEqual([d["is_loop"] for d in decls], [False, True, True, False])
        self.assertEqual([d["sorry"] for d in decls], [False, False, False, True])
        self.assertRegex(decls[0]["text"], check.RAW_PTR_TYPES)
        self.assertEqual(decls[0]["start"], (1, 0))


@unittest.skipUnless(SWAP_LEAN.exists() and SQUARE_LEAN.exists(), "recorded attempts not present")
class GeneratedLeanParsing(unittest.TestCase):
    """lean_decls() on Lean that Aeneas actually generated (committed with the attempts)."""

    def test_swap_list_declarations(self):
        decls = {d["lean"]: d for d in check.lean_decls(SWAP_LEAN)}
        axioms = {k for k, d in decls.items() if d["kind"] == "axiom"}
        self.assertEqual(axioms, {"core.ptr.swap", "core.ptr.mut_ptr.RawPtrMutT.add", "alloc.vec.Vec.as_mut_ptr"})
        self.assertEqual(decls["swap_List"]["kind"], "def")
        self.assertFalse(decls["swap_List"]["sorry"])
        self.assertEqual(decls["core.ptr.swap"]["rust"], "core::ptr::swap")
        for ax in axioms:
            self.assertRegex(decls[ax]["text"], check.RAW_PTR_TYPES, ax)
            self.assertIn("note", check.axiom_entry(ax, decls[ax], "mbpp_591_swap_List"))

    def test_square_nums_axioms_have_no_note(self):
        decls = {d["lean"]: d for d in check.lean_decls(SQUARE_LEAN)}
        axioms = [d for d in decls.values() if d["kind"] == "axiom"]
        self.assertEqual(len(axioms), 3)
        for d in axioms:
            self.assertNotIn("note", check.axiom_entry(d["lean"], d, "mbpp_8_square_nums"))
            self.assertEqual(check.axiom_origin(d["rust"], "mbpp_8_square_nums"), "stdlib")


if __name__ == "__main__":
    unittest.main()
