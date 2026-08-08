#!/usr/bin/env python3
"""Compose GitHub release notes from the build manifests.

Describes what was published: one row per PDF with its variant, section order,
page count and size, followed by the commit and workflow that produced them.

The page budget is deliberately not applied here — an over-length résumé is
review-time feedback, so that warning belongs on the PR, not on a release that
has already been merged.
"""

from typing import Final

import cli
from build_manifest import Build, env

INTRO: Final = "Rolling build of `main`."
DOWNLOAD_URL: Final = "{repo}/releases/download/latest/{file}"
TABLE_HEADER: Final = (
    "| PDF | Variant | Section order | Pages | Size |",
    "|---|---|---|---|---|",
)


def downloads(builds: list[Build], repo: str) -> list[str]:
    """A table of every published PDF, linked to its release asset."""

    def row(build: Build) -> str:
        url = DOWNLOAD_URL.format(repo=repo, file=build.file)
        return (
            f"| [{build.file}]({url}) | {build.variant.capitalize()} "
            f"| {build.section_order} | {build.pages} | {build.size} |"
        )

    return ["## Downloads", "", *TABLE_HEADER, *map(row, builds)]


def provenance(builds: list[Build], repo: str) -> list[str]:
    """Where these PDFs came from: commit, workflow run, engine."""
    sha = env("COMMIT_SHA")
    engines = sorted({build.engine for build in builds})
    dates = sorted({build.date for build in builds if build.date})

    return [
        "## Build",
        "",
        f"- Commit [`{sha[:7]}`]({repo}/commit/{sha}) by {env('COMMIT_AUTHOR')}",
        f"- Committed {env('COMMIT_TIME')}",
        f"- Workflow [run #{env('RUN_NUMBER')}]({env('RUN_URL')})",
        f"- Built {', '.join(dates)} with {', '.join(engines)}",
        "",
        "<details>",
        "<summary>Commit message</summary>",
        "",
        "```",
        env("COMMIT_MSG"),
        "```",
        "",
        "</details>",
    ]


def main() -> None:
    args = cli.io_args(__doc__, source="build", output="notes.md")
    builds = cli.load_builds(args.source)
    repo = env("REPO_URL")

    cli.write(
        args.output,
        [INTRO, "", *downloads(builds, repo), "", *provenance(builds, repo), ""],
        subject=f"from {len(builds)} manifest(s)",
    )


if __name__ == "__main__":
    cli.run(main)
