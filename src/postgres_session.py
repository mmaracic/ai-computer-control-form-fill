"""PostgreSQL-based session storage for the AI Computer Control Form Fill service."""

import json

import psycopg
from agents import SessionABC
from agents.items import TResponseInputItem
from psycopg import sql

COL_ID: str = "id"
COL_SESSION_ID: str = "session_id"
COL_ITEM: str = "item"
COL_CREATED_AT: str = "created_at"


class PostgresSession(SessionABC):
    """PostgreSQL-based session implementation for storing conversation history.

    This implementation uses a PostgreSQL database to persist session data, allowing
    for scalable and durable storage of conversation history across multiple sessions.
    """

    _conninfo: str
    _schema_name: str
    _table_name: str
    _schema_ident: sql.Identifier
    _table_ident: sql.Identifier

    def __init__(
        self,
        session_id: str,
        conninfo: str,
        schema_name: str,
        table_name: str,
    ) -> None:
        """Initialize the session with connection details and table configuration.

        Args:
            session_id: Unique identifier for this session.
            conninfo: PostgreSQL connection info string (DSN or keyword arguments).
            schema_name: PostgreSQL schema in which the session table resides.
            table_name: Name of the table used to store session items.

        """
        self.session_id = session_id
        self._conninfo = conninfo
        self._schema_name = schema_name
        self._table_name = table_name
        self._schema_ident = sql.Identifier(schema_name)
        self._table_ident = sql.Identifier(schema_name, table_name)
        self._initialize()

    def _initialize(self) -> None:
        """Create the schema and session table if they do not already exist."""
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
            sql.Identifier(COL_SESSION_ID),
            sql.Identifier(COL_ITEM),
            sql.Identifier(COL_CREATED_AT),
        )
        with psycopg.connect(self._conninfo, autocommit=True) as conn:
            conn.execute(create_schema_sql)
            conn.execute(create_table_sql)

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Retrieve the conversation history for this session.

        Args:
            limit: Maximum number of items to retrieve. If None, retrieves all items.
                   When specified, returns the latest N items in chronological order.

        Returns:
            List of input items representing the conversation history.

        """
        select_sql = sql.SQL(
            "SELECT {} FROM {} WHERE {} = %s ORDER BY {} ASC",
        ).format(
            sql.Identifier(COL_ITEM),
            self._table_ident,
            sql.Identifier(COL_SESSION_ID),
            sql.Identifier(COL_ID),
        )
        select_limited_sql = sql.SQL(
            "SELECT {col} FROM ("
            "SELECT {col}, {id} FROM {tbl} WHERE {sid} = %s ORDER BY {id} DESC LIMIT %s"
            ") sub ORDER BY {id} ASC",
        ).format(
            col=sql.Identifier(COL_ITEM),
            id=sql.Identifier(COL_ID),
            tbl=self._table_ident,
            sid=sql.Identifier(COL_SESSION_ID),
        )
        async with await psycopg.AsyncConnection.connect(self._conninfo) as conn:
            if limit is None:
                cursor = await conn.execute(select_sql, (self.session_id,))
            else:
                cursor = await conn.execute(
                    select_limited_sql,
                    (self.session_id, limit),
                )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Add new items to the conversation history.

        Args:
            items: List of input items to add to the history.

        """
        insert_sql = sql.SQL(
            "INSERT INTO {} ({}, {}) VALUES (%s, %s::jsonb)",
        ).format(
            self._table_ident,
            sql.Identifier(COL_SESSION_ID),
            sql.Identifier(COL_ITEM),
        )
        async with (
            await psycopg.AsyncConnection.connect(
                self._conninfo,
                autocommit=True,
            ) as conn,
            conn.cursor() as cur,
        ):
            await cur.executemany(
                insert_sql,
                [(self.session_id, json.dumps(item)) for item in items],
            )

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from the session.

        Returns:
            The most recent item if the session is not empty, otherwise None.

        """
        pop_sql = sql.SQL(
            "DELETE FROM {tbl} WHERE {id} = ("
            "SELECT {id} FROM {tbl} WHERE {sid} = %s ORDER BY {id} DESC LIMIT 1"
            ") RETURNING {col}",
        ).format(
            tbl=self._table_ident,
            id=sql.Identifier(COL_ID),
            sid=sql.Identifier(COL_SESSION_ID),
            col=sql.Identifier(COL_ITEM),
        )
        async with await psycopg.AsyncConnection.connect(
            self._conninfo,
            autocommit=True,
        ) as conn:
            cursor = await conn.execute(pop_sql, (self.session_id,))
            row = await cursor.fetchone()
            return row[0] if row is not None else None

    async def clear_session(self) -> None:
        """Delete all items for this session from the database."""
        clear_sql = sql.SQL(
            "DELETE FROM {} WHERE {} = %s",
        ).format(
            self._table_ident,
            sql.Identifier(COL_SESSION_ID),
        )
        async with await psycopg.AsyncConnection.connect(
            self._conninfo,
            autocommit=True,
        ) as conn:
            await conn.execute(clear_sql, (self.session_id,))
