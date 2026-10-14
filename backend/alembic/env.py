"""Environnement Alembic (Jour 6).

- URL : variable d'environnement ``MIGRATION_DATABASE_URL``, celle du **propriétaire du
  schéma**, jamais ``alembic.ini`` ni le rôle applicatif (``app/db/roles.py``). Un appel
  depuis le code (tests) la passe par ``config.attributes["migration_database_url"]``.
  L'URL est vérifiée sans qu'aucun fragment n'apparaisse dans un message d'erreur.
- Sécurité d'exécution : verrou consultatif (deux migrations simultanées s'attendent),
  ``lock_timeout`` (une migration qui attend un verrou échoue au lieu de bloquer le trafic).
- Métadonnées : toutes les tables déclarées dans ``app/modules/*/models.py``
  (``app.db.registry``), avec la convention de nommage de ``app.db.base``.
- Autogénération : types et valeurs par défaut serveur comparés. Les contraintes ``CHECK``
  ne sont **pas** comparées par Alembic : toute modification d'une liste de valeurs fait
  l'objet d'une migration écrite à la main (indexes-and-constraints.md §3.5).
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import parse_database_url
from app.db.registry import load_metadata

MIGRATION_URL_VARIABLE = "MIGRATION_DATABASE_URL"
# Clé du verrou consultatif des migrations (pg_advisory_xact_lock). Registre des clés :
# indexes-and-constraints.md §7 ; toute nouvelle clé y est déclarée pour éviter une collision.
MIGRATION_LOCK_KEY = 7_302_418_559_001
# Une migration qui attend un verrou plus longtemps échoue (SQLSTATE 55P03) : proposé, Q-103.
MIGRATION_LOCK_TIMEOUT = "10s"

config = context.config

# Lancé depuis le code (tests), Alembic ne reconfigure pas la journalisation : la
# configuration de l'application est conservée et son nettoyage s'applique.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    # disable_existing_loggers=False : les journaux de l'application restent actifs.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = load_metadata()


def get_database_url() -> str:
    """Renvoie l'URL des migrations, ou échoue clairement sans jamais en citer une partie."""
    url = config.attributes.get("migration_database_url") or os.environ.get(MIGRATION_URL_VARIABLE)
    if not url:
        raise RuntimeError(f"{MIGRATION_URL_VARIABLE} n'est pas définie : voir .env.example.")
    try:
        parse_database_url(url)
    except ValueError as exc:
        # Message fixe : jamais un fragment de l'URL, qui contient le mot de passe.
        raise RuntimeError(str(exc).replace("DATABASE_URL", MIGRATION_URL_VARIABLE)) from None
    return url


def _guard_statements() -> list[str]:
    """Verrou consultatif, puis délai d'attente des verrous des migrations.

    Une seconde migration simultanée **attend** la première (`lock_timeout` désactivé le
    temps de prendre le verrou consultatif) ; ensuite, toute attente de verrou de plus de
    10 s fait échouer la migration au lieu de bloquer le trafic. Le verrou est libéré avec
    la transaction.
    """
    return [
        "SET LOCAL lock_timeout = 0",
        f"SELECT pg_advisory_xact_lock({MIGRATION_LOCK_KEY})",
        f"SET LOCAL lock_timeout = '{MIGRATION_LOCK_TIMEOUT}'",
    ]


def run_migrations_offline() -> None:
    """Génère le SQL des migrations sans connexion à la base."""
    context.configure(
        url=get_database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        # Le SQL généré porte les mêmes protections que l'exécution en ligne.
        for statement in _guard_statements():
            context.execute(statement)
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        for statement in _guard_statements():
            connection.execute(text(statement))
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
