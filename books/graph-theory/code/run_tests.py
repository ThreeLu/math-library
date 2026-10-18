"""Run the Python code printed in the combinatorial-optimization lectures.

Every ``lstlisting`` block with ``language=Python`` (and without ``style=frag``)
is executed in book order, so a lecture may use what earlier lectures defined
(as a reader would); then ``tests/test_<lecture>.py`` checks the functions
against brute force or networkx.  Usage (from the repository root or anywhere):

    python3 books/graph-theory/code/run_tests.py            # all lectures
    python3 books/graph-theory/code/run_tests.py traversal  # one lecture
"""
import importlib.util
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
LECTURES = HERE.parent / "lectures"
BLOCK = re.compile(r"\\begin\{lstlisting\}\[([^\]]*)\]\n(.*?)\\end\{lstlisting\}", re.S)


def code_of(lecture):
    text = (LECTURES / f"{lecture}.tex").read_text(encoding="utf-8")
    parts = [body for opts, body in BLOCK.findall(text)
             if "language=Python" in opts and "style=frag" not in opts]
    return "\n\n".join(parts)


def book_order():
    main = (HERE.parent / "graph-theory.tex").read_text(encoding="utf-8")
    return re.findall(r"\\input\{lectures/([^}]+)\}", main)


def run(lecture):
    ns = {"__name__": f"lecture_{lecture}"}
    for name in book_order():
        exec(compile(code_of(name), f"<{name}.tex>", "exec"), ns)
        if name == lecture:
            break
    test = HERE / "tests" / f"test_{lecture}.py"
    if test.exists():
        spec = importlib.util.spec_from_file_location(f"test_{lecture}", test)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.check(ns)
    return ns


def main():
    names = sys.argv[1:] or sorted(p.stem[5:] for p in (HERE / "tests").glob("test_*.py"))
    failed = 0
    for name in names:
        try:
            run(name)
            print(f"ok    {name}")
        except Exception:
            failed += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
