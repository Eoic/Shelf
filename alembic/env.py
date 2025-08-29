import asyncio
import pathlib
import sys

sys.path.append(str((pathlib.Path(__file__).parent.parent.parent).resolve()))

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from database.base import Base

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode, supporting async engine.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    config_section = config.get_section(config.config_ini_section, {})
    url = config_section.get("sqlalchemy.url") or config.get_main_option(
        "sqlalchemy.url",
    )

    if url and url.startswith("postgresql+asyncpg"):
        # Use async engine for async DB URLs
        connectable = create_async_engine(url, poolclass=pool.NullPool)

        async def run_async_migrations():
            async with connectable.connect() as connection:
                await connection.run_sync(
                    lambda sync_conn: context.configure(
                        connection=sync_conn,
                        target_metadata=target_metadata,
                    ),
                )
                async with connection.begin():
                    await connection.run_sync(context.run_migrations)

        asyncio.run(run_async_migrations())
    else:
        # Fallback to sync engine for sync DB URLs
        connectable = engine_from_config(
            config_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
