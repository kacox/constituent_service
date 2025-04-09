import logging
import os
import sqlite3
from dataclasses import asdict
from datetime import date

from flask import request, send_file, Flask

from db import DB_NAME, Constituent, ConstituentsTable


app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_constituents_csv_file(month: str = None, year: str = None):
    """
    TODO: Ideally the required CSV files would be pre-generated.

    We could have two periodically running tasks:
        - Once a day for the year + day level reports. The task would
            generate a CSV file for the previous day's sign ups.
        - Once a year (on New Year's Day) for year level reports. The
            task would generate a CSV for the prior year's sign ups.

    These tasks could store the CSV files somewhere like AWS S3.

    This function would know the naming and path conventions used by the
    tasks that create the CSV files. It could then generate the file
    path and file name and return them to the caller.

    E.g.
        If given just the year 2024, it could give the appropriate file
        path and file name for the 2024 sign ups CSV stored in S3.
    """

    return "dummy_file.csv", "dummy_file.csv"


@app.route("/constituents", methods=["GET"])
def get_all_constituents():
    limit = request.args.get("limit", 20)
    offset = request.args.get("offset", 0)

    filters = {}
    county = request.args.get("county")
    if county:
        filters["county"] = county

    constituents = ConstituentsTable.get_constituents(limit, offset, filters)
    paginated_constituents_response = {
        "results": constituents,
        "offset": offset,
        "limit": limit
    }
    return paginated_constituents_response


@app.route("/constituents", methods=["POST"])
def create_constituent():
    # TODO: change error handling to have JSON formatted response to client
        # when there is an uncaught exception
    # TODO: validate incoming fields (e.g. email, address info, etc)
    try:
        constituent_to_create = Constituent(
            first_name=request.json["first_name"],
            last_name=request.json["last_name"],
            email=request.json["email"],
            address={
                "house_number": request.json["address"]["house_number"],
                "street": request.json["address"]["street"],
                "unit_or_apartment": request.json["address"].get("unit_or_apartment"),
                "city": request.json["address"]["city"],
                "state": request.json["address"]["state"],
                "zip_code": request.json["address"]["zip_code"],
                "county": request.json["address"]["county"],
            },
            signed_up=date.today().strftime("%Y-%m-%d"),
        )
    except KeyError as err:
        logging.error("A required field for Constituent is missing")
        print(err)
        return {"error": "Missing a required field"}, 400

    existing_constituent = ConstituentsTable.get_constituent_by_email(request.json["email"])
    if existing_constituent:
        merged_constituent = Constituent(
            first_name=constituent_to_create.first_name,
            last_name=constituent_to_create.last_name,
            email=constituent_to_create.email,
            address={
                "house_number": constituent_to_create.address.house_number,
                "street": constituent_to_create.address.street,
                "unit_or_apartment": constituent_to_create.address.unit_or_apartment,
                "city": constituent_to_create.address.city,
                "state": constituent_to_create.address.state,
                "zip_code": constituent_to_create.address.zip_code,
                "county": constituent_to_create.address.county,
            },
            signed_up=existing_constituent.signed_up,
        )
        ConstituentsTable.update_constituent_by_email(merged_constituent)
        return asdict(merged_constituent)
    else:
        new_constituent = ConstituentsTable.create_constituent(constituent_to_create)
        return asdict(new_constituent)


@app.route("/constituents/csv", methods=["GET"])
def get_constituents_csv():
    # TODO: validate month and year values
    month = request.args.get("month")
    year = request.args.get("year")

    filters = {}
    if month and not year:
        return {"error": "Must provide year when providing month"}, 400
    elif month and year:
        file_path, file_name = get_constituents_csv_file(month, year)
    elif year:
        file_path, file_name = get_constituents_csv_file(year)
    else:
        return {"error": "Must provide year and optionally month"}, 400

    if file_path and file_name:
        return send_file(file_path, as_attachment=True, download_name=file_name)
    else:
        return {"error": "Unable to retrieve CSV file"}, 500

def setup_db():
    """Create the necessary table(s)"""
    conn = sqlite3.connect(DB_NAME)
    with conn:
        cur = conn.cursor()

        # see if tables were already made
        res = cur.execute("SELECT name FROM sqlite_master")
        if not res.fetchone():
            logging.info("Creating tables...")
            # SQLite does not have a date or datetime data type; using a text type
            cur.execute("CREATE TABLE constituents(first_name varchar(255) NOT NULL,last_name varchar(255) NOT NULL,email varchar(255) UNIQUE NOT NULL,house_number INT NOT NULL,street varchar(255) NOT NULL,unit_or_apartment varchar(10),city varchar(255) NOT NULL,state varchar(2) NOT NULL,zip_code varchar(255) NOT NULL,county varchar(255) NOT NULL,created_at varchar(255) NOT NULL)")

            seed_data = (
                {
                    "first_name": "Helly",
                    "last_name": "Rhoades",
                    "email": "heyrhoades5@gmail.com",
                    "house_number": 90,
                    "street": "Lumon St.",
                    "unit_or_apartment": "B",
                    "city": "Somewhere",
                    "state": "PA",
                    "zip_code": "18195",
                    "county": "Lehigh",
                    "created_at": "2025-04-01",
                },
                {
                    "first_name": "John",
                    "last_name": "Bob",
                    "email": "jbob23@yahoo.com",
                    "house_number": 1234,
                    "street": "Place St.",
                    "unit_or_apartment": None,
                    "city": "Somewhere",
                    "state": "NJ",
                    "zip_code": "08111",
                    "county": "Sussex",
                    "created_at": "2025-04-09",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane123smith@outlook.com",
                    "house_number": 6,
                    "street": "Other Ave.",
                    "unit_or_apartment": None,
                    "city": "Townie",
                    "state": "NJ",
                    "zip_code": "08113",
                    "county": "Sussex",
                    "created_at": "2025-04-09",
                },
            )
            cur.executemany("insert into constituents values(:first_name, :last_name, :email, :house_number, :street, :unit_or_apartment, :city, :state, :zip_code, :county, :created_at)", seed_data)
            logging.info("Done creating tables...")
        else:
            logging.info("Tables already created...")
    # Connection object used as context manager only commits or rollbacks transactions,
    # so the connection object should be closed manually
    conn.close()


setup_db()
