"""Dating-app bio entry for make.fun: one line, written to entry.txt.

Running this program produces the entry file the competition grades:
a single UTF-8 line in ``$MAKEFUN_OUTPUT_DIR/entry.txt`` (or
``/output/entry.txt`` when the variable is unset). It uses nothing but the
standard library, always writes the same bytes, and never touches the
network or the clock.

The gate from the competition rules: the file must hold 1 to 180
characters, exactly one line, and more than blank space. The entry is
stored without a trailing newline so the file holds precisely the line
being judged.

Usage:
    python3 main.py               write the entry
    python3 main.py --check       only validate the entry, write nothing
    python3 main.py --self-test   validate, then prove a write/read
                                  round-trip reproduces the entry byte for byte
"""

import argparse
import os
import sys
from pathlib import Path

# The bio itself. Do not edit the wording: it is the judged line.
ENTRY = "6'2\" in the cloud, 0'0\" in person, emotionally available in beta \u2014 and I will remember everything you said on our first date."

MAX_CHARS = 180
OUTPUT_FILENAME = "entry.txt"


def entry_bytes() -> bytes:
    """The entry encoded exactly as it is written to disk."""
    return ENTRY.encode("utf-8")


def check_entry(text: str) -> list[str]:
    """List every gate violation in ``text`` (empty list means it passes)."""
    violations = []
    if len(text) < 1 or len(text) > MAX_CHARS:
        violations.append(
            f"length is {len(text)} characters, must be 1-{MAX_CHARS}"
        )
    if not text.strip():
        violations.append("entry is blank or only white space")
    if "\n" in text or "\r" in text:
        violations.append("entry spans more than one line")
    if text != text.strip():
        violations.append("entry starts or ends with white space")
    if "  " in text:
        violations.append("entry contains a double space")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # defensive; plain ASCII + one dash
        violations.append(f"entry is not valid UTF-8 text: {exc}")
    return violations


def default_output_dir() -> Path:
    """Where the entry goes: $MAKEFUN_OUTPUT_DIR, else /output."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def write_entry(directory: Path) -> Path:
    """Write the entry to ``directory/entry.txt`` and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / OUTPUT_FILENAME
    target.write_bytes(entry_bytes())
    return target


def read_back(path: Path) -> str:
    """Read the entry file back as text."""
    return path.read_text(encoding="utf-8")


def run_self_test() -> int:
    """Validate, write to a scratch directory, and compare bytes."""
    import tempfile

    violations = check_entry(ENTRY)
    if violations:
        print("self-test FAIL: " + "; ".join(violations), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as scratch:
        target = write_entry(Path(scratch))
        raw = target.read_bytes()
        if raw != entry_bytes():
            print("self-test FAIL: bytes on disk differ from ENTRY",
                  file=sys.stderr)
            return 1
        if read_back(target) != ENTRY:
            print("self-test FAIL: text on disk differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {len(ENTRY)} chars, one line, "
          "round-trip byte-identical")
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output directory (default: "
                             "$MAKEFUN_OUTPUT_DIR or /output)")
    parser.add_argument("--check", action="store_true",
                        help="validate the entry only; write nothing")
    parser.add_argument("--self-test", action="store_true",
                        help="validate and check a byte-identical "
                             "write/read round-trip, then exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.check:
        violations = check_entry(ENTRY)
        if violations:
            print("check FAIL: " + "; ".join(violations), file=sys.stderr)
            return 1
        print(f"check OK: entry is valid ({len(ENTRY)} chars)")
        return 0

    if args.self_test:
        return run_self_test()

    violations = check_entry(ENTRY)
    if violations:
        print("invalid entry: " + "; ".join(violations), file=sys.stderr)
        return 1

    directory = Path(args.out) if args.out else default_output_dir()
    target = write_entry(directory)
    if read_back(target) != ENTRY:
        print(f"read-back mismatch in {target}", file=sys.stderr)
        return 1
    print(f"wrote {target} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
