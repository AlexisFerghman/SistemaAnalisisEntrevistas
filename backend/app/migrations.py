"""Migraciones de esquema idempotentes para la persistencia de la sesión única.

La migración se ejecuta al arrancar (`init_db`) porque el proyecto no usa Alembic y solo
mantiene dos tablas. Cada paso consulta el catálogo antes de aplicar DDL, de modo que una
segunda ejecución no falla ni modifica el contenido.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

SESSION_TABLE = "current_session"
EXPORT_TABLE = "current_export"


def _table_exists(connection: Connection, table: str) -> bool:
    return (
        connection.execute(
            text("SELECT to_regclass(:name)"),
            {"name": f"public.{table}"},
        ).scalar()
        is not None
    )


def _column_type(connection: Connection, table: str, column: str) -> str | None:
    return connection.execute(
        text(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    ).scalar()


def _primary_key_name(connection: Connection, table: str) -> str | None:
    return connection.execute(
        text(
            """
            SELECT con.conname
            FROM pg_constraint AS con
            JOIN pg_class AS rel ON rel.oid = con.conrelid
            JOIN pg_namespace AS nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'public'
              AND rel.relname = :table
              AND con.contype = 'p'
            LIMIT 1
            """
        ),
        {"table": table},
    ).scalar()


def _drop_primary_key(connection: Connection, table: str) -> None:
    name = _primary_key_name(connection, table)
    if name:
        safe_name = name.replace('"', '""')
        connection.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT "{safe_name}"'))


def upgrade(engine: Engine) -> None:
    """Aplica `json` → `jsonb` y `id text` → `id uuid` de forma idempotente."""
    with engine.begin() as connection:
        if not _table_exists(connection, SESSION_TABLE):
            return

        if _column_type(connection, SESSION_TABLE, "created_at") is None:
            connection.execute(
                text(
                    "ALTER TABLE current_session "
                    "ADD COLUMN created_at timestamptz NOT NULL DEFAULT now()"
                )
            )

        for table in (SESSION_TABLE, EXPORT_TABLE):
            if not _table_exists(connection, table):
                continue
            payload_type = _column_type(connection, table, "payload")
            if payload_type and payload_type != "jsonb":
                connection.execute(
                    text(
                        f"ALTER TABLE {table} "
                        "ALTER COLUMN payload TYPE jsonb USING payload::jsonb"
                    )
                )

        id_type = _column_type(connection, SESSION_TABLE, "id")
        if id_type and id_type != "uuid":
            if _column_type(connection, SESSION_TABLE, "session_uuid") is None:
                connection.execute(
                    text("ALTER TABLE current_session ADD COLUMN session_uuid uuid")
                )
            connection.execute(
                text(
                    "UPDATE current_session "
                    "SET session_uuid = gen_random_uuid() "
                    "WHERE session_uuid IS NULL"
                )
            )
            connection.execute(
                text(
                    "UPDATE current_session "
                    "SET payload = jsonb_set("
                    "payload, '{session_id}', to_jsonb(session_uuid::text), true"
                    ") "
                    "WHERE payload->>'session_id' IS DISTINCT FROM session_uuid::text"
                )
            )
            _drop_primary_key(connection, SESSION_TABLE)
            connection.execute(text("ALTER TABLE current_session DROP COLUMN id"))
            connection.execute(
                text("ALTER TABLE current_session RENAME COLUMN session_uuid TO id")
            )
            connection.execute(
                text("ALTER TABLE current_session ALTER COLUMN id SET NOT NULL")
            )
            connection.execute(
                text("ALTER TABLE current_session ADD PRIMARY KEY (id)")
            )
            connection.execute(
                text(
                    "ALTER TABLE current_session "
                    "ALTER COLUMN id SET DEFAULT gen_random_uuid()"
                )
            )
        else:
            connection.execute(
                text(
                    "ALTER TABLE current_session "
                    "ALTER COLUMN id SET DEFAULT gen_random_uuid()"
                )
            )
            connection.execute(
                text(
                    "UPDATE current_session "
                    "SET payload = jsonb_set("
                    "payload, '{session_id}', to_jsonb(id::text), true"
                    ") "
                    "WHERE payload->>'session_id' IS DISTINCT FROM id::text"
                )
            )


def downgrade(engine: Engine) -> None:
    """Revierte el esquema al estado anterior. Solo es válido con una única fila."""
    with engine.begin() as connection:
        if not _table_exists(connection, SESSION_TABLE):
            return

        payload_type = _column_type(connection, SESSION_TABLE, "payload")
        if payload_type == "jsonb":
            connection.execute(
                text(
                    "UPDATE current_session "
                    "SET payload = jsonb_set("
                    "payload, '{session_id}', to_jsonb('session-current'::text), true"
                    ")"
                )
            )
        else:
            connection.execute(
                text(
                    "UPDATE current_session "
                    "SET payload = jsonb_set("
                    "payload::jsonb, '{session_id}', to_jsonb('session-current'::text), true"
                    ")::json"
                )
            )

        id_type = _column_type(connection, SESSION_TABLE, "id")
        if id_type == "uuid":
            _drop_primary_key(connection, SESSION_TABLE)
            connection.execute(
                text("ALTER TABLE current_session ADD COLUMN legacy_id text")
            )
            connection.execute(
                text("UPDATE current_session SET legacy_id = 'current'")
            )
            connection.execute(text("ALTER TABLE current_session DROP COLUMN id"))
            connection.execute(
                text("ALTER TABLE current_session RENAME COLUMN legacy_id TO id")
            )
            connection.execute(
                text("ALTER TABLE current_session ALTER COLUMN id SET NOT NULL")
            )
            connection.execute(
                text("ALTER TABLE current_session ADD PRIMARY KEY (id)")
            )

        if _column_type(connection, SESSION_TABLE, "created_at") is not None:
            connection.execute(
                text("ALTER TABLE current_session DROP COLUMN created_at")
            )

        for table in (SESSION_TABLE, EXPORT_TABLE):
            if not _table_exists(connection, table):
                continue
            payload_type = _column_type(connection, table, "payload")
            if payload_type == "jsonb":
                connection.execute(
                    text(
                        f"ALTER TABLE {table} "
                        "ALTER COLUMN payload TYPE json USING payload::json"
                    )
                )
