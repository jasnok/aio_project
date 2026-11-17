"""Parse tldr Markdown without performing network requests."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    description: str
    command: str


@dataclass(frozen=True)
class Page:
    title: str
    description: str
    examples: tuple[Example, ...]


def parse_page(markdown: str) -> Page:
    """Extract descriptions and examples, preserving command contents exactly."""
    title = ""
    description = []
    examples = []
    pending = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
        elif stripped.startswith(">"):
            description.append(stripped[1:].strip())
        elif stripped.startswith("- "):
            pending = stripped[2:].strip()
        elif stripped.startswith("`") and stripped.endswith("`") and pending is not None:
            examples.append(Example(pending, stripped[1:-1]))
            pending = None
    return Page(title, "\n".join(description), tuple(examples))
