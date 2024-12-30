# Trustpilot Technical Challenge

## Overview

A simple toy application that demonstrates API that allows CRUD operations to be performed on Trustpilot Review dataset. See the [Design Doc](./docs/design-doc.md) for a more detailed overview of the design.

## Run

Application has been containerised using a Docker image. To get started using the API, build the run the Docker image.

- Build image - `docker build -t reviews-fastapi:0.1 .`

- Run container - `docker run -it -p 8000:8000 -e DATABASE_PASSPHRASE="acb123" reviews-fastapi:0.1`
  <!-- - To persist the database run - `docker run -it -v ./volume/reviews.db:/app/reviews.db -p 8000:8000 nlm` -->
  - The API will be at http://localhost:8000/
  - View the Swagger API docs at http://localhost:8000/docs

## Testing

Run `uv run pytest` from root directory to run test suite.

To get test coverage run `uv run coverage run --branch --source=src -m pytest && uv run coverage report -m`
