"""Utilies and classes for accessing data from the SQLite DB."""
import sqlite3
from dataclasses import asdict, dataclass

DB_NAME = "constituent_service.db"
_SQLITE_CONN = None


def get_connection(testing=False):
    """Manages the connection to the SQLite database.

    In production would use SQLAlchemy to manage connection pool.
    """
    global _SQLITE_CONN
    if not _SQLITE_CONN:
        if testing:
            _SQLITE_CONN = sqlite3.connect(":memory:")
        else:
            _SQLITE_CONN = sqlite3.connect(DB_NAME)
        _SQLITE_CONN.row_factory = sqlite3.Row
    return _SQLITE_CONN


@dataclass
class Address:
    """
    TODO need to add validation on multiple fields such as:
        - state: must be two letters (ideally this would be an ENUM)
        - zipcode: should be 5 digits (it's a string because python does not
            accept integers leading with 0)
        - signed_up: should be a  ISO 8601 string (YYYY-MM-DD)
    """

    house_number: int
    street: str
    city: str
    state: str
    zip_code: str
    county: str
    unit_or_apartment: str | None = None


@dataclass
class Constituent:
    """
    TODO need to add validation on multiple fields such as:
        - email: use a regex for format
        - signed_up: should be a  ISO 8601 string (YYYY-MM-DD)
    """

    first_name: str
    last_name: str
    email: str
    address: dict
    signed_up: str | None = None

    def __post_init__(self):
        self.address = Address(**self.address)

    def as_flat_dict(self):
        nested_dict = asdict(self)
        address_info = nested_dict["address"]

        flat_dict = {}
        for key, val in nested_dict.items():
            if key != "address":
                if key == "signed_up":
                    flat_dict["created_at"] = val
                else:
                    flat_dict[key] = val
        flat_dict.update(address_info)

        return flat_dict


def _row_to_constituent(row: sqlite3.Row):
    if not row:
        return None
    return Constituent(
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        address={
            "house_number": row["house_number"],
            "street": row["street"],
            "unit_or_apartment": row["unit_or_apartment"],
            "city": row["city"],
            "state": row["state"],
            "zip_code": row["zip_code"],
            "county": row["county"],
        },
        signed_up=row["created_at"],
    )


class ConstituentsTable:
    """An interface to get data from the book table."""

    def create_constituent(constituent_to_create: Constituent):
        conn = get_connection()
        # TODO: validation (TypeError) should be caught and raised
        fields = Constituent.as_flat_dict(constituent_to_create)
        with conn:
            cur = conn.cursor()
            res = cur.execute(
                "insert into constituents values(:first_name, :last_name, :email, :house_number, :street, :unit_or_apartment, :city, :state, :zip_code, :county, :created_at)",
                fields,
            )
            if res.rowcount == 1:
                # rowid is an implicit column (PK) in SQLite
                res = cur.execute(
                    f"SELECT *, rowid from constituents where rowid={res.lastrowid};"
                )
                new_constituent_row = res.fetchone()
            else:
                raise Exception("Failed to create new constituent")

        new_constituent = _row_to_constituent(new_constituent_row)
        return new_constituent

    def get_constituent_by_email(email: str):
        conn = get_connection()
        cur = conn.cursor()
        email_to_escape = (email,)
        res = cur.execute(
            "SELECT * FROM constituents where email=?;", email_to_escape
        )
        constituent_row = res.fetchone()

        return _row_to_constituent(constituent_row)

    def get_constituents(limit, offset, filters: dict = {}) -> list:
        query = "SELECT * FROM constituents LIMIT ? OFFSET ?;"

        # TODO: SQLAlchemy will make adding filters cleaner
        # TODO: only works for one filter right now
        if filters:
            table_name_idx = query.find("constituents")
            # +13 on first slice includes the space
            query = (
                query[:table_name_idx + 13]
                + f"WHERE county = ? "
                + query[table_name_idx + 13:]
            )
            county = filters["county"]

        conn = get_connection()
        cur = conn.cursor()
        if filters:
            res = cur.execute(
                query, (county, limit, offset)
            )
        else:
            res = cur.execute(query, (limit, offset))
        constituent_rows = res.fetchall()

        constituents = []
        for row in constituent_rows:
            constituent = _row_to_constituent(row)
            constituents.append(constituent)

        return constituents

    def update_constituent_by_email(constituent_to_update: Constituent):
        fields = Constituent.as_flat_dict(constituent_to_update)

        conn = get_connection()
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE constituents SET first_name=:first_name, last_name=:last_name, house_number=:house_number, street=:street, unit_or_apartment=:unit_or_apartment, city=:city, state=:state, zip_code=:zip_code, county=:county WHERE email=:email;", fields)

            updated_constituent_row = cur.execute(
                f"SELECT * from constituents WHERE email='{constituent_to_update.email}';"
            )
            updated_constituent_row = updated_constituent_row.fetchone()

        return _row_to_constituent(updated_constituent_row)
