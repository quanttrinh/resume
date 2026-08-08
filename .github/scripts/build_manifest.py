"""Shared model for the sidecar manifests the Makefile writes beside each PDF.

Every build records how it was made — variant, section-order flags, page count,
size, engine — in `<name>.json`. The release notes, the PR comment and the
preview site all read those manifests instead of re-deriving anything from file
names, so they can only describe what the build actually did.

The page budget lives here but is applied only by the PR preview: page count is
review-time feedback, not something worth flagging on a published release.
"""

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Final, NamedTuple, Self

__all__ = ["KB", "PAGE_BUDGET", "SECTION_FLAGS", "WARN", "Build", "Pages", "env"]

WARN: Final = "⚠️"
KB: Final = 1024

#: Manifest flag -> label, in the order the sections appear on the page.
SECTION_FLAGS: Final = (("skills_bottom", "Skills"), ("education_bottom", "Education"))


def env(name: str, default: str = "") -> str:
    """Read an environment variable, treating an empty value as unset."""
    return os.environ.get(name) or default


#: Pages allowed before the PR preview flags a build; 0 disables the check.
#: Set by the workflow from the PAGE_BUDGET repo variable.
PAGE_BUDGET: Final = int(env("PAGE_BUDGET", "1"))


class Pages(NamedTuple):
    """A page count rendered for display, plus whether it busts the budget."""

    text: str
    over_budget: bool


@dataclass(frozen=True, slots=True)
class Build:
    """One built PDF, as recorded by the Makefile."""

    file: str
    variant: str
    skills_bottom: bool = False
    education_bottom: bool = False
    pages: str = "?"
    bytes: int = 0
    date: str = ""
    engine: str = "unknown"

    @classmethod
    def from_manifest(cls, path: Path) -> Self:
        """Build one instance, ignoring manifest keys this version predates."""
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})

    @classmethod
    def load_all(cls, directory: Path) -> list[Self]:
        """Every manifest in `directory`, ordered by file name."""
        return [cls.from_manifest(path) for path in sorted(directory.glob("*.json"))]

    @property
    def section_order(self) -> str:
        """Human-readable section order, straight from the recorded flags."""
        moved = [label for key, label in SECTION_FLAGS if getattr(self, key)]
        return f"{' + '.join(moved)} moved below Experience" if moved else "Default"

    @property
    def page_count(self) -> Pages:
        """Page count, marked with WARN when it exceeds PAGE_BUDGET."""
        if not self.pages.isdigit() or PAGE_BUDGET <= 0:
            return Pages(self.pages, False)
        over = int(self.pages) > PAGE_BUDGET
        return Pages(f"{self.pages} {WARN}" if over else self.pages, over)

    @property
    def size(self) -> str:
        """Human-readable file size."""
        kb = self.bytes / KB
        return f"{kb:.0f} KB" if kb < KB else f"{kb / KB:.1f} MB"

    @property
    def description(self) -> str:
        """Short prose summary: variant and how the sections were ordered."""
        return f"{self.variant.capitalize()} · {self.section_order}"


def over_budget(builds: list[Build]) -> list[str]:
    """File names of the builds that exceed the page budget."""
    return [build.file for build in builds if build.page_count.over_budget]
