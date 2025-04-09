# Constituent Service

A basic backend service with RESTful HTTP endpoints that allow an elected
official to:

  - List all the constituents that are currently in the system
  - Submit new constituent contact data
  - Export a csv file of constituent contact data filtered by sign up time

## API

### GET /constituents
List endpoint for all constituents. Includes pagination and some basic filtering options.

Endpoint paginates based on the provided query parameters:
- `offset`: How many entries there are prior to the start of the returned list;
    the default is 0.
- `limit`: The maximum number of items to return in one page; the default is 20.

```
# Sample request
curl -X GET http://127.0.0.1:5000/constituents?limit=1

# Sample response
{
  "results": [
    {
      "first_name": "John",
      "last_name": "Bob",
      "email": "jbob23@yahoo.com",
      "address": {
        "house_number": 1234,
        "street": "Place St."
        "unit_or_apartment": null,
        "city": "Somewhere",
        "state": "NJ",
        "zip_code": "08111",
        "county": "Sussex"
      },
      signed_up: "2025-04-09"
    }
  ],
  "offset": 0,
  "limit": 1,
}

# To get the next page
curl -X GET 'http://127.0.0.1:5000/book?limit=1&offset=1'
```

Filtering options:
- `county`: the constituent's county name

```
# Sample request
curl -X GET http://127.0.0.1:5000/constituents?county=Sussex

# Sample response
{
  "results": [
    {
      "first_name": "John",
      "last_name": "Bob",
      "email": "jbob23@yahoo.com",
      "address": {
        "house_number": 1234,
        "street": "Place St."
        "unit_or_apartment": null,
        "city": "Somewhere",
        "state": "NJ",
        "zip_code": "08111",
        "county": "Sussex"
      },
      signed_up: "2025-04-09"
    }
  ],
  "offset": 0,
  "limit": 20,
}
```

### POST /constituents
Submit new constituent contact data. Must provide a request payload with:
```
{
  "first_name": "Helly",
  "last_name": "Rhoades",
  "email": "heyrhoades5@gmail.com",
  "address": {
    "house_number": 90,
    "street": "Lumon St.",
    "unit_or_apartment": "B",  // OPTIONAL
    "city": "Somewhere",
    "state": "PA",
    "zip_code": "18195",
    "county": "Lehigh"
  }
}
```

Example valid request:
```
curl -X POST -H 'Content-Type: application/json' -d '{"first_name": "Helly", "last_name": "Rhoades", "email": "heyrhoades5@gmail.com", "address": {"house_number": 90, "street": "Lumon St.", "unit_or_apartment": "B", "city": "Somewhere", "state": "PA", "zip_code": "18195", "county": "Lehigh"}}' 'http://127.0.0.1:5000/constituents'
```

### GET /constituents/csv
Download a csv file of constituent contact data filtered by sign up time.

Filtering options:
- `year`: the year a constituent signed up
- `month`: the month a constituent signed up; if month is provided, year MUST also be provided.

```
# Sample request
curl -X GET http://127.0.0.1:5000/constituents/csv?year=2025
```

**Note: this endpoint returns a dummy CSV file. See comments in the source code.**

## Development
For local development, activate a virtual environment (e.g. using python's `venv` module) then install required libraries found in the `requirements.txt` file.

Python 3.11.2 was used to develop this project.

```
# create the virtual environment with a compatible version of Python
python -m venv path_for_your_venv

# activate the virtual environment
source path_for_your_venv/bin/activate

# install the required libraries
pip install -r requirements.txt

# now you can run the webserver from the project directory!
```

Run the webserver locally by running this from the project directory:
```
flask run --reload
```
