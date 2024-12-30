# Trustpilot Technical Challenge

## Overview

A simple toy application that demonstrates API that allows CRUD operations to be performed on Trustpilot Review dataset. See the [Design Doc](./docs/design-doc.md) for a more detailed overview of the design.

## Testing

Run `uv run pytest` from root directory to run test suite.

To get test coverage run `uv run coverage run --branch --source=src -m pytest && uv run coverage report -m`
