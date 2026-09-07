# Résumé

My résumé in LaTeX. Content lives in `resume.tex`; every layout decision lives
in `resumestyle.sty` as a named length or flag.

## Build

Tools and tasks are managed by [mise](https://mise.jdx.dev)
(`brew install mise`). One command fetches the pinned Tectonic and latexindent:

```sh
mise install
```

That also installs the git pre-commit hook, via a `postinstall` hook in
`mise.toml`; it is skipped in CI.

```sh
mise run             # full variant  -> build/resume-full.pdf
mise run short       # short variant -> build/resume-short.pdf
mise run all         # every variant
mise watch build     # rebuild on change (needs watchexec)
mise run clean
mise tasks           # list everything
```

Versions live in `mise.toml`, resolved into `mise.lock`; mise verifies each
download's checksum and, where published, its SLSA provenance. chktex is the
exception — it ships inside TeX Live and publishes no standalone release, so
CI installs the pinned Ubuntu package and locally it comes with MacTeX.

Each PDF gets a `build/<name>.json` sidecar recording how it was built; CI reads
those instead of parsing file names.

### Format and lint

```sh
mise run fmt         # format the sources in place (latexindent)
mise run check       # fmt-check + lint, what CI gates on
```

Formatting is [latexindent](https://latexindent.readthedocs.io), configured in
`.latexindent.yaml`. It reflows: each paragraph is unwrapped and rewrapped at
100 columns, so editing a sentence never leaves a ragged line behind. Two
settings there are load-bearing and easy to lose — `-m` (passed by the fmt
task), without which every `modifyLineBreaks` option is ignored silently,
and `lookForPreamble: .tex: 0`, without which the whole file is skipped, since
the sections live in `\newcommand` bodies in the preamble.

Hand-aligned regions are fenced with `%\begin{noindent}` … `%\end{noindent}`;
the tunables table in `resumestyle.sty` relies on it.

`mise install` writes `.git/hooks/pre-commit` as a shim: it exports the staged
paths as `$STAGED` and runs the `pre-commit` task, so the logic stays tracked in
`mise-tasks/pre-commit`. It formats the staged `.tex`/`.sty` files, re-stages
them, then runs chktex — the same two gates as CI. chktex must come from TeX
Live/MacTeX to get the full check locally; without it the lint step is a
notice, not a failure. Skip a run with `git commit -n`.

A file that is only *partially* staged is refused rather than formatted,
since re-staging it would sweep in the unstaged edits.

### Knobs

Pass options to the build task, or set the equivalent environment variables:

| Variable | Default | Effect |
|---|---|---|
| `VARIANT` | `full` | Which variant to build (`full` drops nothing, `short` omits Projects) |
| `SKILLS_BOTTOM` | `0` | `1` moves Skills below Experience |
| `EDUCATION_BOTTOM` | `0` | `1` moves Education below Experience |
| `PAGE_BUDGET` | `1` | Warn above this many pages; `0` disables |
| `FIRST_PAGE_ONLY` | `0` | `1` keeps only the first PDF page |
| `ENGINE` | `tectonic` | LaTeX engine |

```sh
mise run build -- --variant short --skills-bottom --education-bottom
mise run build -- --variant full --first-page-only
VARIANT=short SKILLS_BOTTOM=1 mise run build # environment variables still work
```

Flags reach LaTeX through a generated `build-vars.tex`; the output name is
tagged accordingly, so variants never overwrite each other.

## Layout

Style knobs are grouped at the top of `resumestyle.sty` — page margin, vertical
rhythm, type sizes, rules, title block, and the section-order flags. The title
block measures the contact column and grows the name to fill whatever space is
left, bounded by `\resumenamemax` and the contact column's own height.

Section order is declared at the bottom of `resume.tex`; each section is a macro,
so reordering is a one-line change.

## CI

| Workflow | Trigger | Does |
|---|---|---|
| `build-resume.yml` | push to `main`, PRs, manual | Builds every variant, uploads artifacts |
| ↳ preview job | PRs | Publishes the PDFs to GitHub Pages under `pr-<n>/` and posts a sticky comment |
| ↳ publish-latest job | push to `main` | Publishes main's build to `latest/`, pinned atop the preview index |
| ↳ release job | push to `main` | Refreshes the rolling `latest` release |
| `pr-preview-cleanup.yml` | PR closed | Drops that PR's directory from the site |

Manual runs (Actions → *Build résumé* → *Run workflow*) take the variant and
section-order flags as inputs. `PAGE_BUDGET` can be overridden with a repo
variable of the same name.

Requires Pages set to **deploy from a branch → `gh-pages` → `/ (root)`**; the
branch is created by the first preview run. Fork PRs are skipped — their token
is read-only.

## Typeface

[XCharter](https://ctan.org/pkg/xcharter) — a Charter derivative with a large
x-height, chosen so the body text holds up at small sizes and on screen.

## Icons

[Font Awesome Free](https://fontawesome.com) via the `fontawesome5` LaTeX
package — glyphs, not image files, so nothing is vendored. Icons are CC BY 4.0,
fonts SIL OFL 1.1.

## Licence

[MIT](LICENSE) — take the style file, tasks and workflows and make them
yours. The biographical content is mine; swap it for your own.
