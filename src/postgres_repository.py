"""PostgresRepository: CRUD operations for a PostgreSQL table storing JSONB items.

This module implements a generic repository for managing JSON data in a PostgreSQL
table, using the psycopg3 library for database interactions. The repository
auto-creates the schema and table on initialization if they do not already exist.
"""

import json
import logging
from datetime import datetime

import psycopg
from psycopg import sql
from pydantic import BaseModel

logger = logging.getLogger(__name__)

COL_ID: str = "id"
COL_DESCRIPTION: str = "description"
COL_DATA: str = "data"
COL_CREATED_AT: str = "created_at"


class RepositoryItem(BaseModel):
    """Represents a single item stored in the repository table."""

    id: int
    description: str
    data: dict
    created_at: datetime


class PostgresRepository:
    """Repository for Postgres database table CRUD operations over JSONB items.

    Args:
        conninfo: PostgreSQL connection info string (DSN or keyword arguments).
        schema_name: PostgreSQL schema in which the table resides.
        table_name: Name of the table used to store items.

    """

    _conninfo: str
    _schema_name: str
    _table_name: str
    _schema_ident: sql.Identifier
    _table_ident: sql.Identifier

    def __init__(
        self,
        conninfo: str,
        schema_name: str,
        table_name: str,
    ) -> None:
        """Initialize the repository with connection details and table configuration.

        Args:
            conninfo: PostgreSQL connection info string (DSN or keyword arguments).
            schema_name: PostgreSQL schema in which the table resides.
            table_name: Name of the table used to store items.

        """
        self._conninfo = conninfo
        self._schema_name = schema_name
        self._table_name = table_name
        self._schema_ident = sql.Identifier(schema_name)
        self._table_ident = sql.Identifier(schema_name, table_name)
        self._initialize()

    def _initialize(self) -> None:
        """Create the schema and table if they do not already exist."""
        create_schema_sql = sql.SQL(
            "CREATE SCHEMA IF NOT EXISTS {}",
        ).format(self._schema_ident)
        create_table_sql = sql.SQL(
            "CREATE TABLE IF NOT EXISTS {} ("
            "{} SERIAL PRIMARY KEY, "
            "{} TEXT NOT NULL, "
            "{} JSONB NOT NULL, "
            "{} TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            ")",
        ).format(
            self._table_ident,
            sql.Identifier(COL_ID),
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_CREATED_AT),
        )
        with psycopg.connect(self._conninfo, autocommit=True) as conn:
            conn.execute(create_schema_sql)
            conn.execute(create_table_sql)

    def create_item(self, description: str, data: dict) -> RepositoryItem:
        """Create a new item in the Postgres DB table.

        Args:
            description: A human-readable label for the item.
            data: The JSON data to store in the item.

        Returns:
            The created item with its assigned id and timestamp.

        """
        insert_sql = sql.SQL(
            "INSERT INTO {} ({}, {}) VALUES (%s, %s::jsonb)"
            " RETURNING {}, {}, {}, {}",
        ).format(
            self._table_ident,
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_ID),
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_CREATED_AT),
        )
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute(insert_sql, (description, json.dumps(data))).fetchone()
        if row is None:
            msg = "INSERT with RETURNING returned no row."
            raise RuntimeError(msg)
        return RepositoryItem(
            id=row[0],
            description=row[1],
            data=row[2],
            created_at=row[3],
        )

    def read_item(self, item_id: int) -> RepositoryItem | None:
        """Read an item from the Postgres DB table by its ID.

        Args:
            item_id: The ID of the item to read.

        Returns:
            The found item, or None if no item with the given id exists.

        """
        select_sql = sql.SQL(
            "SELECT {}, {}, {}, {} FROM {} WHERE {} = %s",
        ).format(
            sql.Identifier(COL_ID),
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_CREATED_AT),
            self._table_ident,
            sql.Identifier(COL_ID),
        )
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute(select_sql, (item_id,)).fetchone()
        if row is None:
            return None
        return RepositoryItem(
            id=row[0],
            description=row[1],
            data=row[2],
            created_at=row[3],
        )

    def read_items_by_description(
        self,
        description: str,
    ) -> list[RepositoryItem]:
        """Find items by exact description match (case-insensitive).

        Args:
            description: The description value to search for. Comparison is
                         case-insensitive via LOWER() on both sides.

        Returns:
            Possibly empty list of matching items ordered by id ascending.

        """
        select_sql = sql.SQL(
            "SELECT {}, {}, {}, {} FROM {} WHERE LOWER({}) = LOWER(%s)"
            " ORDER BY {} ASC",
        ).format(
            sql.Identifier(COL_ID),
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_CREATED_AT),
            self._table_ident,
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_ID),
        )
        with psycopg.connect(self._conninfo) as conn:
            rows = conn.execute(select_sql, (description,)).fetchall()
        return [
            RepositoryItem(id=r[0], description=r[1], data=r[2], created_at=r[3])
            for r in rows
        ]

    def update_item(
        self,
        item_id: int,
        description: str,
        data: dict,
    ) -> RepositoryItem | None:
        """Update the description and data of an existing item in the Postgres DB table.

        Args:
            item_id: The ID of the item to update.
            description: The new human-readable label for the item.
            data: The new JSON data to store in the item.

        Returns:
            The updated item, or None if no item with the given id exists.

        """
        update_sql = sql.SQL(
            "UPDATE {} SET {} = %s, {} = %s::jsonb"
            " WHERE {} = %s RETURNING {}, {}, {}, {}",
        ).format(
            self._table_ident,
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_ID),
            sql.Identifier(COL_ID),
            sql.Identifier(COL_DESCRIPTION),
            sql.Identifier(COL_DATA),
            sql.Identifier(COL_CREATED_AT),
        )
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute(
                update_sql,
                (description, json.dumps(data), item_id),
            ).fetchone()
        if row is None:
            return None
        return RepositoryItem(
            id=row[0],
            description=row[1],
            data=row[2],
            created_at=row[3],
        )

    def delete_item(self, item_id: int) -> bool:
        """Delete an item from the Postgres DB table by its ID.

        Args:
            item_id: The ID of the item to delete.

        Returns:
            True if an item was deleted, False if no item with the given id existed.

        """
        delete_sql = sql.SQL(
            "DELETE FROM {} WHERE {} = %s",
        ).format(
            self._table_ident,
            sql.Identifier(COL_ID),
        )
        with psycopg.connect(self._conninfo) as conn:
            result = conn.execute(delete_sql, (item_id,))
        return result.rowcount > 0
