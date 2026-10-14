"""Environnement Alembic : squelette du Jour 4, finalisé au Jour 6.

L'URL de connexion vient de la variable d'environnement ``DATABASE_URL``, jamais
d'``alembic.ini``, pour qu'aucun mot de passe ne soit versionné. Au Jour 6, elle sera
lue par l'objet de configuration de l'application, et ``target_metadata`` désignera
la base déclarative.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import parse_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aucune table au Jour 4 : la base déclarative est créée au Jour 6.
target_metadata = None


def get_database_url() -> str:
    """Renvoie l'URL de la base, ou échoue clairement sans jamais en citer une partie."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL n'est pas définie : voir .env.example.")
    try:
        parse_database_url(url)
    except ValueError as exc:
        # Message fixe : jamais un fragment de l'URL, qui contient le mot de passe.
        raise RuntimeError(str(exc)) from None
    return url


def run_migrations_offline() -> None:
    """Génère le SQL des migrations sans connexion à la base."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Applique les migrations avec un moteur asynchrone, sans pool de connexions."""
    connectable = create_async_engine(get_database_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
