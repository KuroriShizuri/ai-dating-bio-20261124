"""One-line dating-app bio entry for make.fun.

Writes the single bio line to entry.txt in the output directory
($MAKEFUN_OUTPUT_DIR, default /output). Stdlib only, deterministic, no
network and no side effects beyond the one output file.

Gate (from the competition rules): /output/entry.txt must be UTF-8 text
of 1 to 180 characters, not only white space. The entry is written with
no trailing newline so the file holds exactly the judged line.

Modes:
  (default)   validate ENTRY, write it, read it back, confirm identical
  --check     validate ENTRY only and exit; writes nothing
  --self-test validate ENTRY and check a byte-identical write/read
              round-trip in a temporary directory, then exit
"""

import argparse
import os
import sys

ENTRY = (
    "6'2\" in the cloud, 0'0\" in person, emotionally available in beta "
    "\u2014 and I will remember everything you said on our first date."
)

# The exact bytes the judges read: the entry encoded once, reused by the
# writer, the self-test and the read-back check so no step can drift.
ENTRY_BYTES = ENTRY.encode("utf-8")

MAX_CHARS = 180


def entry_bytes() -> bytes:
    """Return the entry as the exact UTF-8 bytes written to entry.txt."""
    return ENTRY_BYTES


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    problems = []
    if not 1 <= len(text) <= MAX_CHARS:
        problems.append(f"length {len(text)} chars, must be 1-{MAX_CHARS}")
    if not text.strip():
        problems.append("entry is only white space")
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    # Other line-breaking characters would also split the judged line.
    if any(c in text for c in ("\x0b", "\x0c", "\u2028", "\u2029")):
        problems.append("entry contains a line-breaking character")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "  " in text:
        problems.append("entry contains a double space")
    if any(ord(c) < 32 for c in text):
        problems.append("entry contains a control character")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "wb") as f:
        f.write(entry_bytes())
    return path


def read_back(path: str) -> bytes:
    """Read entry.txt back as raw bytes for a byte-exact comparison."""
    with open(path, "rb") as f:
        return f.read()


def self_test() -> int:
    """Validate ENTRY and check a byte-identical write/read round-trip."""
    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        raw = read_back(path)
        if raw != entry_bytes():
            print("self-test FAIL: read-back bytes differ from ENTRY",
                  file=sys.stderr)
            return 1
        if raw.decode("utf-8") != ENTRY:
            print("self-test FAIL: read-back text differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {len(ENTRY)} chars, single line, "
          f"byte-identical round-trip")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output directory (default: "
                             "$MAKEFUN_OUTPUT_DIR or /output)")
    parser.add_argument("--self-test", action="store_true",
                        help="validate ENTRY and check a byte-identical "
                             "write/read round-trip, then exit")
    parser.add_argument("--check", action="store_true",
                        help="validate ENTRY only (no file written) and exit")
    args = parser.parse_args(argv)

    if args.check:
        problems = validate(ENTRY)
        if problems:
            print("check FAIL: " + "; ".join(problems), file=sys.stderr)
            return 1
        print(f"check OK: ENTRY valid ({len(ENTRY)} chars)")
        return 0

    if args.self_test:
        return self_test()

    problems = validate(ENTRY)
    if problems:
        print("invalid ENTRY: " + "; ".join(problems), file=sys.stderr)
        return 1

    out_dir = args.out or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = write_entry(out_dir)
    # Read back and confirm the file holds exactly the entry, byte for byte.
    if read_back(path) != entry_bytes():
        print(f"read-back mismatch in {path}", file=sys.stderr)
        return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
