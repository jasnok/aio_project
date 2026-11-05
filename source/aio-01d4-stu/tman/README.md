# tman

Stage 1: read Korean tldr pages as plain terminal text. Textual TUI and man
support are reserved for later stages.

Requires Python 3.11+ and uv.

```sh
uv run tman tar
uv run pytest
```

Pages come from https://github.com/tldr-pages/tldr, using
`pages.ko/common/<command>.md` first and `pages.ko/linux/<command>.md` only
when the common page returns HTTP 404. Each request has a 10-second timeout.
Command contents inside backticks are preserved, including tldr placeholders.

Errors go to stderr. Exit codes: 1 for a missing page, 2 for a network error
or invalid arguments, and 3 for a timeout. Successful reads exit with 0.
Tests use fixed Markdown and mocked requests; they do not access the internet.

The virtual environment, environment files, and caches are ignored by Git.
Commit `uv.lock` to preserve reproducible dependency versions.
