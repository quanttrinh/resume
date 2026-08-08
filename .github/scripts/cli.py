"""Argument parsing and error handling shared by the CI scripts.

Keeps each script's `main()` down to the work it actually does: parse, load the
manifests, write a file.

Parsed arguments come back as typed namespaces rather than plain
`argparse.Namespace`, whose `__getattr__` returns `Any` and defeats type
checking at the call site.
"""

import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Sequence
from pathlib import Path

from build_manifest import Build

__all__ = ["Failure", "IOArgs", "io_args", "load_builds", "run", "write"]


class Failure(Exception):
    """Something the operator should fix; reported without a traceback."""


class IOArgs(Namespace):
    """A `<source-dir> <output-file>` invocation."""

    source: Path
    output: Path


def io_args(description: str | None, *, source: str, output: str) -> IOArgs:
    """Parse the standard `<source-dir> <output-file>` pair."""
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "source",
        nargs="?",
        default=source,
        type=Path,
        help=f"directory of build manifests (default: {source})",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=output,
        type=Path,
        help=f"file to write (default: {output})",
    )
    return parser.parse_args(namespace=IOArgs())


def load_builds(directory: Path) -> list[Build]:
    """Every manifest in `directory`, or a Failure if there are none."""
    builds = Build.load_all(directory)
    if not builds:
        raise Failure(f"no build manifests found in {directory}/")
    return builds


def write(path: Path, lines: Sequence[str], *, subject: str) -> None:
    """Write joined `lines` and report what was produced."""
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path} {subject}")


def run(main: Callable[[], None]) -> None:
    """Invoke `main`, turning a Failure into a clean non-zero exit."""
    try:
        main()
    except Failure as failure:
        print(f"error: {failure}", file=sys.stderr)
        raise SystemExit(1) from None
