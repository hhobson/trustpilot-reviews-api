# Trustpilot Technical Challenge

## Overview

A simple toy application that demonstrates API that allows CRUD operations to be performed on Trustpilot Review dataset. See the [Design Doc](./docs/design-doc.md) for a more detailed overview of the design, including assumptions, functional and non-functional design decisions and next steps. A few elements of the design have yet to be implemented, notably API Pagination and Authentication.

The API has been built with the [FastAPI Framework](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/) (a thin abstraction layer on top of Pydantic and SQLAlchemy) and SQLite backend.

## How to Use API

This API has been containerised using Docker, so to get started you will need to have [Docker installed](https://www.docker.com/get-started/) on your machine.

From the root directory of the repo, run:

- Build image - `docker build -t reviews-fastapi:latest .`

- Run container - `docker run -it -p 8000:8000 -e DATABASE_PASSPHRASE="abc123" -e DATABASE_PASSPHRASE="abc123" reviews-fastapi:latest`
  - You should change the passphrase to something much stronger. You can store this in a .env file and use the `--env-file` flag rather than `-e`

The API will be then be avaliable at <http://localhost:8000/> on your machine and you can view the API docs <http://localhost:8000/docs>. The docs will take you though the avaliable endpoints and allow you try them out.

 [!Warning]
> Currently the database can't be persisted after the container stops. So all data created and edited will be lost once the container stops.
<!-- Command once database can be persisted `docker run -it -e DATABASE_PASSPHRASE="abc123" -v ./volume/reviews.db:/app/reviews.db -p 8000:8000 reviews-fastapi:latest` -->

## Development Setup

### EditorConfig

This project has [EditorConfig](https://editorconfig.org/) setup to enable a consistent coding style for the project across multiple IDEs and Operating systems. Most major IDEs support EditorConfig, either [out of the box](https://editorconfig.org/#pre-installed) or [via a plugin](https://editorconfig.org/#download).

- VS Code needs [EditorConfig plugin](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig) to be installed

- PyCharm just requires [EditorConfig support to be enabled](https://www.jetbrains.com/help/pycharm/settings-code-style.html#EditorConfig) in Editor Preferences

### UV

This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies and virtual environment. To get started:

- Make sure uv is installed - See [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) if not

- From project root directory run `uv sync` to create virtual environment and install dependencies or update one if it has been created previously

### Tests

This project uses [pytest](https://docs.pytest.org/en/stable/) framework for testing.

Tests can be run locally by either:

1. Via the terminal by running `uv run pytest`

1. Via your IDE, see configuration examples for [VS Code](https://code.visualstudio.com/docs/python/testing) or [PyCharm](https://www.jetbrains.com/help/pycharm/creating-run-debug-configuration-for-tests.html)

To get test coverage run `uv run coverage run --branch --source=src -m pytest && uv run coverage report -m`

No automated testing via CI/CD pipeline is currently set up for this project.

### Linting & Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for Python linting and formatting.

Ruff can be run locally by either:

1. Via the terminal by running:
    - Linting: `uv run ruff check`
      - run `uv run ruff check --fix` to have ruff automagically correct issues where possible
    - Formatting: `uv run ruff format`

1. Automatically on each commit with [pre-commit](#pre-commit)

No automated Linting via CI/CD pipeline is currently set up for this project.

### Pre-Commit

[pre-commit](https://pre-commit.com/) is set up to run a check suite of code quality tests locally on each commit. These include [Ruff](https://docs.astral.sh/ruff/), [yamllint](https://github.com/DavidAnson/markdownlint?tab=readme-ov-file#markdownlint) and [markdownlint](https://yamllint.readthedocs.io/en/stable/). See [pre-commit config file](./.pre-commit-config.yaml) for all hooks.

The checks will only run on the files that have changed during your commit, so they are usually pretty fast and do not slow down your development speed. If any checks fail then the commit will be stopped. Where possible the issues will be automatically fixed, so you can just inspect the changes and stage the files for committing.

To pre-commit run `poetry run pre-commit install`
