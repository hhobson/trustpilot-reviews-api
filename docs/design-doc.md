# Design Doc

## Introduction

### Overview

Design for an api that allows CRUD operations to be performed on Trustpilot Review dataset.

### Background

The objective is to build an api as an interface for a database containing the Trustpilot Review dataset. The api needs to allow business users to perform CRUD operations on the dataset.

As a take home task, this will be a toy application akin to a Proof of Concept. The code should be written to a production standard, but the architecture will not be production ready. There should be a route to production that doesn't require significant code changes and any unhandled edge cases should be highlighted.

### Assumptions

The design has been build on the basis of the following assumptions. These have been made without consultation as this is a take home test with limited requirement details and no opportunity to get clarity.

- Use cases for the api are transactional in nature - with only the current state required
- API is for business users only
- The api is expected to return all the data including any Personally Identifiable Information (PII) fields
- The CSV data is only for initial population of the database and the ability to update the database from a CSVs is not a required feature
- Despite the [sample data](../data/dataops_tp_reviews.csv) being very small, it is assumed to be representation of the data the system should handle
- All reviews must be made by a legitimate user, so must have a valid email address

### Out of Scope

## Solution

### Functional Design

#### Data Notes

- The data is UTF-8 encoded
- "Review Content" column can contain emojis
- PII columns and other free text columns with PII risk, see [PII section](#personally-identifiable-information) for more details
- Not all emails in "Email Address" column are valid
- "Review Rating" is on a scale between 1 & 5
- "Country" column has a mix of country names and codes (which are not [ISO 3166](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) compliant)

#### Data Pipeline

As CSV data is just for initial population of the database, the ingestion will be run as part api container startup. Once the api is instantiated, all changes to the database should be done via the API.

Functionality:

- Check if email field is valid email address - if not exclude data as without email, not possible to establish is review is legitimate (if issue then email validation should be implamed at collection)
- Convert emojis to text
- Convert country field to ISO-3166 country code or name

#### Data Store

For simplicity will use an embedded database stored locally within api container. As this is a transactional system, will use [SQLite](https://www.sqlite.org/).

Ingestion and API design should be setup so that it would be straight forward to switch a different database running on external server.

##### Data Model

The data contains two clear entities Reviewer and Review, with a one-to-many relationship.

Reviewer....

- `reviewer_id` - **??** - should this be uuid or just use email encripted value?
- `reviewer_email` - **TEXT** (PII) - shouldn't be stored in plain text
- `reviewer_name` - **TEXT** (PII) - shouldn't be stored in plain text
- `reviewer_country` - **TEXT** - should store be ISO-3166 country code or name

Review....

- `review_id` - **INT**
- `review_title` - **TEXT**
- `review_rating` - **TEXT**
- `review_content` - **TEXT**
- `review_date` - **DATE**

#### API

API paths should map to the data model, with `/reviewers` and `/reviews`

##### Reviewers PATH

- GET `/reviewers` : Get all reviewers
- POST `/reviewers` : Create a new reviewer

- GET `/reviewers/{id}` : Get the reviewer by id
- PUT `/reviewers/{id}` : Update the reviewer by id
- DELETE `/reviewers/{id}` : Delete the reviewer by id

##### Reviews PATH

- GET `/reviews` : Get all reviews
- POST `/reviews` : Create a new review

- GET `/reviews/{id}` : Get the review by id
- PUT `/reviews/{id}` : Update the review by id
- DELETE `/reviews/{id}` : Delete the review by id

### Non-Functional Design

#### Personally Identifiable Information

`reviewer_name` ("Reviewer Name" in CSV), `reviewer_email` ("Email Address" in CSV) and `reviewer_country` ("Country" in CSV) columns are PII. `reviewer_name` and `reviewer_email` should be encrypted in the database, `country` will then be pseudo-anonymised.

`review_title` ("Review Title" in CSV) and `review_content` ("Review Content" in CSV) are free text columns and could contain PII. While this is a risk, handling this is out of current scope.

#### Monitoring & Alerting

As a toy application, beyond logging no monitoring or alterting will be implamented.

#### Authentication

Use simple API token for security... This can be set via environment variable for now

## Further Considerations

### Future Improvements and Optimisations

- Consider integrating a proper authentication system like OAuth2 or JWT for more robust security
- Implament OpenTelemetry as ASGI middleware that could then be exported to any OpenTelemetry compliant backend.
- Detecting and handling any PII in free text fields
- Offer separate endpoints that returns reviewer without pii in plane
