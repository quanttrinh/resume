#!/usr/bin/env python3
"""Compose the sticky PR comment pointing at the GitHub Pages preview.

GitHub does not render PDFs inside a comment, so the comment stays a summary:
one row per build linking to the PDF on the preview site, where the document is
embedded and readable in place.
"""

from typing import Final

import cli
from build_manifest import PAGE_BUDGET, WARN, Build, env, over_budget

HEADING: Final = "## 📄 Résumé preview"
SITE_LINK: Final = "**[Open the preview site]({url})** — every PDF rendered in the browser."
TABLE_HEADER: Final = (
    "| PDF | Variant | Section order | Pages | Size |",
    "|---|---|---|---|---|",
)

#: Identifies our comment so pushes edit it rather than adding a new one. The
#: workflow greps for this exact string.
MARKER: Final = "<!-- resume-pr-preview -->"


def summary(builds: list[Build], base_url: str) -> list[str]:
    """A table of every build, linked to the PDF on the preview site."""

    def row(build: Build) -> str:
        return (
            f"| [{build.file}]({base_url}/{build.file}) | {build.variant.capitalize()} "
            f"| {build.section_order} | {build.page_count.text} | {build.size} |"
        )

    return [*TABLE_HEADER, *map(row, builds)]


def budget_warning(builds: list[Build]) -> list[str]:
    """A callout naming any build that runs longer than the page budget."""
    if not (overlong := over_budget(builds)):
        return []
    plural = "" if PAGE_BUDGET == 1 else "s"
    names = ", ".join(f"`{name}`" for name in overlong)
    return ["", f"> {WARN} Longer than {PAGE_BUDGET} page{plural}: {names}."]


def footer() -> list[str]:
    """Provenance line: which commit this preview came from."""
    return [
        "",
        "---",
        "",
        f"Built from `{env('HEAD_SHA')[:7]}` · "
        f"[build artifacts]({env('RUN_URL')}#artifacts) · "
        "the preview refreshes on every push",
    ]


def main() -> None:
    args = cli.io_args(__doc__, source="preview", output="comment.md")
    builds = cli.load_builds(args.source)
    base_url = env("PREVIEW_BASE_URL")

    cli.write(
        args.output,
        [
            MARKER,
            HEADING,
            "",
            SITE_LINK.format(url=base_url),
            "",
            *summary(builds, base_url),
            *budget_warning(builds),
            *footer(),
        ],
        subject=f"covering {len(builds)} PDF(s)",
    )


if __name__ == "__main__":
    cli.run(main)
