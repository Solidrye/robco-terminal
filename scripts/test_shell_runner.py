"""
Phase 1 test: Shell runner without any Pygame/UI.
Run from project root:  python scripts/test_shell_runner.py
(or set PYTHONPATH to project root)
"""
import os
import sys
import time

# Allow importing src when run as script from project root or from scripts/
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.shell.shell_runner import ShellRunner


def main():
    print("Phase 1 test: ShellRunner (no UI)")
    runner = ShellRunner()
    print("Started shell, waiting 0.5s for prompt...")
    time.sleep(0.5)
    lines_before = runner.get_output_lines()
    print(f"Lines so far: {len(lines_before)}")
    for i, line in enumerate(lines_before[:15]):
        print(f"  [{i}] {line!r}")
    if len(lines_before) > 15:
        print(f"  ... and {len(lines_before) - 15} more")

    print("\nSending: echo hello")
    runner.write("echo hello")
    print("Waiting 0.5s for output...")
    time.sleep(0.5)
    lines_after = runner.get_output_lines()
    print(f"Lines now: {len(lines_after)}")
    for i, line in enumerate(lines_after[-10:]):
        print(f"  [{len(lines_after) - 10 + i}] {line!r}")

    if any("hello" in line for line in lines_after):
        print("\nPASS: 'hello' appeared in output.")
    else:
        print("\nFAIL: 'hello' not found in output.")
        return 1
    print("Phase 1 test done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
