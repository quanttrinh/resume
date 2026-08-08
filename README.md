# Résumé

My résumé in LaTeX. Content lives in `resume.tex`; every layout decision lives
in `resumestyle.sty` as a named length or flag.

## Build

Needs [Tectonic](https://tectonic-typesetting.github.io) (`brew install tectonic`).
`pdfinfo` (poppler) is optional — without it the page count is recorded as `?`.

```sh
make            # full variant  -> build/resume-full.pdf
make short      # short variant -> build/resume-short.pdf
make all        # every variant
make watch      # rebuild on change (needs entr)
make clean
```

Each PDF gets a `build/<name>.json` sidecar recording how it was built; CI reads
those instead of parsing file names.

### Knobs

| Variable | Default | Effect |
|---|---|---|
| `VARIANT` | `full` | Which variant to build (`full` drops nothing, `short` omits Projects) |
| `SKILLS_BOTTOM` | `0` | `1` moves Skills below Experience |
| `EDUCATION_BOTTOM` | `0` | `1` moves Education below Experience |
| `PAGE_BUDGET` | `1` | Warn above this many pages; `0` disables |
| `ENGINE` | `tectonic` | LaTeX engine |

```sh
make bottom                        # both sections last
make VARIANT=short SKILLS_BOTTOM=1 # combine freely
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

## Icons

[Font Awesome Free](https://fontawesome.com) via the `fontawesome5` LaTeX
package — glyphs, not image files, so nothing is vendored. Icons are CC BY 4.0,
fonts SIL OFL 1.1.

## Licence

[MIT](LICENSE) — take the style file, Makefile and workflows and make them
yours. The biographical content is mine; swap it for your own.
