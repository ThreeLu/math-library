# Math Library

Lecture notes, research notes and surveys, written in LaTeX and published as a website.

- Books are registered in [`library.yml`](library.yml); each lives in `books/<slug>/`.
- `make site` compiles every book and renders the website into `site/_site/`; `make preview` serves it locally.
- Pushing to `main` publishes the site via GitHub Actions (`.github/workflows/publish.yml`).

See [`AGENTS.md`](AGENTS.md) for how the conversion works and the conventions it relies on.
