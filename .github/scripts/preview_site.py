#!/usr/bin/env python3
"""Generate the HTML for the GitHub Pages preview site.

Two commands, both writing an `index.html`:

    preview_site.py pr      <dir> <pr-number>   one PR: every PDF, embedded
    preview_site.py release <dir>               the current build of main
    preview_site.py root    <site-dir>          landing page listing them all

A directory is listed by the landing page once it has an `index.html`; the
label comes from `.label` beside it, and a `.pinned` marker floats it to the
top (the release preview writes one).

The per-PR page reads the build manifests copied alongside the PDFs, and embeds
the documents themselves — the browser renders them, so nothing is rasterised.
"""

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
import html
import re
from pathlib import Path
from string import Template
from typing import Final

import cli
from build_manifest import WARN, Build, env

SITE_TITLE: Final = "Résumé previews"
GITHUB: Final = env("GITHUB_SERVER_URL", "https://github.com")
PR_DIR: Final = re.compile(r"^pr-(\d+)$")
LABEL_FILE: Final = ".label"     # display name for the landing page
PINNED_FILE: Final = ".pinned"   # presence floats an entry to the top
RELEASE_LABEL: Final = "Latest build (main)"
VIEWER_HEIGHT: Final = "92vh"  # the PDF is the page; chrome stays out of its way

#: Inline so the site needs no assets and no Jekyll processing. A Template
#: rather than an f-string because CSS is full of braces.
STYLE: Final = Template("""
:root { color-scheme: light dark; }
body { font: 13px/1.5 system-ui, sans-serif; margin: 0; padding: 0 1rem 1rem;
       color: color-mix(in srgb, CanvasText 60%, transparent); }
.bar, figcaption { display: flex; gap: .6rem; flex-wrap: wrap; padding: .5rem 0; }
a { color: inherit; text-decoration: none; }
a:hover { color: CanvasText; text-decoration: underline; }
figcaption a:nth-of-type(1) { margin-left: auto; }
figure { margin: 0 0 1rem; scroll-margin-top: .5rem; }
.bar span:last-child a { margin-left: .6rem; }
object { display: block; width: 100%; height: $height; border: 0; }
h1 { color: CanvasText; font-size: 1.6rem; font-weight: 600; text-align: center;
     margin: 3.5rem 0 0; }
ul { list-style: none; margin: 2rem auto; padding: 0; max-width: 26rem; }
li a { display: block; padding: 1rem; border: 1px solid #8883; border-radius: 6px;
       margin-bottom: .5rem; }
li a:hover { color: CanvasText; text-decoration: none; border-color: currentColor; }
""").substitute(height=VIEWER_HEIGHT)

PAGE: Final = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>$style</style>
</head>
<body>
$body
</body>
</html>
""")


def link(text: str, href: str) -> str:
    """An anchor, or plain text when there is nowhere to point it."""
    safe = html.escape(text)
    return f'<a href="{html.escape(href)}">{safe}</a>' if href else safe


def source_links(pr_number: str) -> str:
    """Repo, PR, branch and commit, linked back to GitHub where known."""
    repo = env("GITHUB_REPOSITORY")
    sha = env("HEAD_SHA")
    branch = env("HEAD_REF")
    base = f"{GITHUB}/{repo}" if repo else ""

    parts = [link(repo or "this repo", base)]
    parts.append(link(f"PR #{pr_number}", f"{base}/pull/{pr_number}" if base else ""))
    if branch:
        parts.append(link(branch, f"{base}/tree/{branch}" if base else ""))
    if sha:
        commit = link(sha[:7], f"{base}/commit/{sha}" if base else "")
        parts.append(f"commit <code>{commit}</code>")
    return " · ".join(parts)


def page(title: str, body: str) -> str:
    """Wrap `body` in the shared document shell."""
    return PAGE.substitute(title=html.escape(title), style=STYLE, body=body)


def anchor(build: Build) -> str:
    """Fragment id for one document, so the jump links can reach it."""
    return re.sub(r"[^a-z0-9]+", "-", build.file.lower()).strip("-")


def jump_nav(builds: list[Build]) -> str:
    """Links between documents; pointless with only one, so omitted."""
    if len(builds) < 2:
        return ""
    links = " ".join(
        f'<a href="#{anchor(b)}">{html.escape(Path(b.file).stem)}</a>' for b in builds
    )
    return f"<span>{links}</span>"


def build_section(build: Build, prev: Build | None, next_: Build | None) -> str:
    """One PDF, filling the viewport, under a single line of caption."""
    flag = f" {WARN}" if build.page_count.over_budget else ""
    name = html.escape(build.file)
    steps = "".join(
        f'<a href="#{anchor(other)}" title="{html.escape(other.file)}">{arrow}</a>'
        for other, arrow in ((prev, "← prev"), (next_, "next →"))
        if other
    )
    return (
        f'<figure id="{anchor(build)}"><figcaption>'
        f"<strong>{name}</strong>"
        f"<span>{build.description} · {build.pages} pages{flag} · {build.size}</span>"
        f"{steps}"
        f'<a href="{name}">open ↗</a>'
        "</figcaption>"
        f'<object data="{name}" type="application/pdf">'
        f'<p>No inline PDF support. <a href="{name}">Download {name}</a>.</p>'
        "</object></figure>"
    )


def sections(builds: list[Build]) -> str:
    """Every document, each linked to its neighbours."""
    return "".join(
        build_section(build, builds[i - 1] if i else None, builds[i + 1] if i + 1 < len(builds) else None)
        for i, build in enumerate(builds)
    )


def write_preview(directory: Path, title: str, context: str, *, pinned: bool = False) -> None:
    """A preview page: a thin context bar, then the documents themselves."""
    builds = cli.load_builds(directory)

    bar = (
        '<div class="bar">'
        '<a href="../">← previews</a>'
        f"<span>{context}</span>"
        f"{jump_nav(builds)}"
        "</div>"
    )
    (directory / "index.html").write_text(
        page(title, bar + sections(builds)), encoding="utf-8"
    )
    (directory / LABEL_FILE).write_text(title, encoding="utf-8")
    if pinned:
        (directory / PINNED_FILE).touch()

    print(f"wrote {directory}/index.html for {len(builds)} PDF(s)")


def entries(site: Path) -> list[tuple[str, str]]:
    """(directory, label) for every rendered preview, pinned first.

    A directory without an `index.html` is skipped: linking to it would give a
    directory listing rather than a preview.
    """
    found = []
    for path in sorted(site.iterdir()):
        if not path.is_dir() or not (path / "index.html").is_file():
            continue
        label_file = path / LABEL_FILE
        label = label_file.read_text(encoding="utf-8").strip() if label_file.is_file() else path.name
        match = PR_DIR.match(path.name)
        found.append(((path / PINNED_FILE).exists(), int(match[1]) if match else 0, path.name, label))

    found.sort(reverse=True)
    return [(name, label) for _, _, name, label in found]


def write_root_page(site: Path) -> None:
    """The landing page: every preview currently published."""
    listed = entries(site)
    if listed:
        items = "".join(
            f'<li><a href="{html.escape(name)}/">{html.escape(label)}</a></li>'
            for name, label in listed
        )
        listing = f"<ul>{items}</ul>"
    else:
        listing = "<p>No previews.</p>"

    (site / "index.html").write_text(page(SITE_TITLE, f"<h1>{SITE_TITLE}</h1>{listing}"), encoding="utf-8")
    print(f"wrote {site}/index.html listing {len(listed)} preview(s)")


def release_links() -> str:
    """Repo, branch and commit for the build published from main."""
    repo = env("GITHUB_REPOSITORY")
    sha = env("HEAD_SHA")
    base = f"{GITHUB}/{repo}" if repo else ""

    parts = [link(repo or "this repo", base)]
    parts.append(link("latest release", f"{base}/releases/tag/latest" if base else ""))
    if sha:
        parts.append(f"commit <code>{link(sha[:7], f'{base}/commit/{sha}' if base else '')}</code>")
    return " · ".join(parts)


class SiteArgs(Namespace):
    """A `preview_site.py` invocation; only some fields apply per command."""

    command: str
    directory: Path
    number: str
    site: Path


def main() -> None:
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    pr = commands.add_parser("pr", help="write the page for one PR")
    pr.add_argument("directory", type=Path, help="that PR's directory on the site")
    pr.add_argument("number", help="pull request number")

    release = commands.add_parser("release", help="write the page for main's build")
    release.add_argument("directory", type=Path, help="the release directory on the site")

    root = commands.add_parser("root", help="write the landing page")
    root.add_argument("site", type=Path, help="root of the site")

    args = parser.parse_args(namespace=SiteArgs())
    match args.command:
        case "pr":
            write_preview(args.directory, f"PR #{args.number} preview", source_links(args.number))
        case "release":
            write_preview(args.directory, RELEASE_LABEL, release_links(), pinned=True)
        case _:
            write_root_page(args.site)

if __name__ == "__main__":
    cli.run(main)
