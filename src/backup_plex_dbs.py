import asyncio
import logging
import sys
from os import environ
from watcher import PlexLocalFileBackupHandler
from hachiko.hachiko import AIOWatchdog

PLEX_CONFIG_DIR = "/config/Library/Application Support/Plex Media Server/"
ENABLE_STRINGS = ["true", "yes", "1", "y"]


def get_environ():
    plex_sql_path = environ.get("PLEX_DB_PATH")
    if plex_sql_path is None:
        plex_sql_path = PLEX_CONFIG_DIR + "Plug-in Support/Databases"
    db_backup_path = environ.get("DB_BACKUP_PATH")
    if db_backup_path is None:
        db_backup_path = "/db-backup"
    enable_metadata_flag = environ.get("ENABLE_METADATA_BACKUP", "False")
    enable_metadata = enable_metadata_flag.lower() in ENABLE_STRINGS
    plex_metadata_path = environ.get("PLEX_METADATA_PATH")
    if plex_metadata_path is None:
        plex_metadata_path = PLEX_CONFIG_DIR + "Metadata"
    metadata_backup_path = environ.get("METADATA_BACKUP_PATH")
    if metadata_backup_path is None:
        metadata_backup_path = "/metadata-backup"
    logging_level = environ.get("LOG_LEVEL", "INFO").upper()
    return (plex_sql_path, db_backup_path,
            plex_metadata_path, metadata_backup_path,
            enable_metadata, logging_level)


def setup_logging(logging_level):
    root = logging.getLogger()
    level = logging.getLevelName(logging_level)
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    return root


async def start_watcher(watcher):
    watcher.start()


def start_watching(plex_sql_path, backup_path,
                   plex_metadata_path, metadata_backup_path,
                   enable_metadata, logging_level):
    logger = setup_logging(logging_level)
    loop = asyncio.get_event_loop()
    logger.info("Using PLEX_DB_PATH %s", plex_sql_path)
    logger.info("Using DB_BACKUP_PATH %s", backup_path)
    logger.info("Using PLEX_METADATA_PATH %s", plex_metadata_path)
    logger.info("Using METADATA_BACKUP_PATH %s", metadata_backup_path)
    db_handler = PlexLocalFileBackupHandler(plex_sql_path,
                                            backup_path,
                                            "SQLite")
    db_watcher = AIOWatchdog(plex_sql_path,
                             event_handler=db_handler)
    if enable_metadata:
        metadata_handler = PlexLocalFileBackupHandler(plex_metadata_path,
                                                      metadata_backup_path,
                                                      "Metadata")
        metadata_watcher = AIOWatchdog(plex_metadata_path,
                                       event_handler=metadata_handler)
    try:
        logger.info("Starting Watchers")
        loop.create_task(start_watcher(db_watcher))
        if enable_metadata:
            loop.create_task(start_watcher(metadata_watcher))
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Stopping Watchers")
        db_watcher.stop()
        if enable_metadata:
            metadata_watcher.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    (plex_sql_path, db_backup_path,
     plex_metadata_path, metadata_backup_path,
     enable_metadata, logging_level) = get_environ()
    start_watching(plex_sql_path, db_backup_path,
                   plex_metadata_path, metadata_backup_path,
                   enable_metadata, logging_level)
