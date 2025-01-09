from typing import Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlcipher3 import dbapi2 as sqlcipher_driver
from sqlmodel import Session as SQLModelSession
from sqlmodel import create_engine, inspect

from .config import DATABASE, DATABASE_PASSPHRASE

engine = create_engine(
    f"sqlite+pysqlcipher://:{DATABASE_PASSPHRASE}@/{DATABASE}",
    module=sqlcipher_driver,
    connect_args={"check_same_thread": False},
)


@event.listens_for(Engine, "connect")
def do_connect(dbapi_connection, connection_record):
    """Disable pysqlite's emitting of the BEGIN statement entirely

    This also stops it from emitting COMMIT before any DDL. See more details at:
        https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    """
    dbapi_connection.isolation_level = None


@event.listens_for(Engine, "begin")
def do_begin(conn):
    """emit own BEGIN"""
    conn.exec_driver_sql("BEGIN")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Event that sets SQLite paramas for each database connection"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute('PRAGMA key = "{DATABASE_PASSPHRASE}";')
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(class_=SQLModelSession, autocommit=False, autoflush=False, bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session


Session = Annotated[SQLModelSession, Depends(get_session)]


def get_table_names():
    """Fetch a list of all table names in the database."""
    table_names = inspect(engine, raiseerr=False).get_table_names()
    return table_names
