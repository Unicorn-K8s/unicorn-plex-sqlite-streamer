from hachiko.hachiko import AIOEventHandler
from os.path import basename, join
from os import remove, stat, chown
import stat as lib_stat
from shutil import copy2, move
import logging


class PlexLocalFileBackupHandler(AIOEventHandler):

    def __init__(self, plex_local_path, backup_path, name):
        super().__init__()
        self._logger = logging.getLogger(name)
        self._backup_path = backup_path
        self._plex_local_path = plex_local_path

    def delete_file(self, path):
        db_file = basename(path)
        delete_path = join(self._backup_path, db_file)
        self._logger.debug("Removing file: %s", delete_path)
        try:
            remove(delete_path)
        except FileNotFoundError:
            self._logger.error("File %s has already been deleted",
                               delete_path)

    def backup_file(self, path):
        self._logger.debug("Original file path: %s", path)
        db_file = basename(path)
        backup_path = join(self._backup_path, db_file)
        self._logger.debug("Backup file path: %s", backup_path)
        try:
            stat_info = stat(path)
            UID = stat_info[lib_stat.ST_UID]
            GID = stat_info[lib_stat.ST_GID]
            copy2(path, backup_path, follow_symlinks=False)
            self._logger.debug("Setting UID:GID %s:%s for %s",
                               UID, GID, backup_path)
            chown(backup_path, UID, GID, follow_symlinks=False)
        except FileNotFoundError:
            self._logger.info("File %s was deleted before it could be copied",
                              path)

    async def on_created(self, event):
        if event.src_path != self._plex_local_path:
            self._logger.info("File created: Backing up %s",
                              basename(event.src_path))
            self.backup_file(event.src_path)

    async def on_moved(self, event):
        if event.src_path != self._plex_local_path:
            self._logger.info("File moved: old: %s, new: %s",
                              basename(event.src_path),
                              basename(event.dest_path))
            db_file = basename(event.src_path)
            db_new_name = basename(event.dest_path)
            old_path = join(self._backup_path, db_file)
            self._logger.debug("Old file path: %s", old_path)
            new_path = join(self._backup_path, db_new_name)
            self._logger.debug("New file path: %s", new_path)
            stat_info = stat(old_path)
            UID = stat_info[lib_stat.ST_UID]
            GID = stat_info[lib_stat.ST_GID]
            move(old_path, new_path)
            self._logger.debug("Setting UID:GID %s:%s for %s",
                               UID, GID, new_path)
            chown(new_path, UID, GID, follow_symlinks=False)

    async def on_modified(self, event):
        if event.src_path != self._plex_local_path:
            self._logger.info("File modified: Backing up %s",
                              basename(event.src_path))
            self.backup_file(event.src_path)

    async def on_deleted(self, event):
        if event.src_path != self._plex_local_path:
            self._logger.info("File deleted: Removing %s",
                              basename(event.src_path))
            self.delete_file(event.src_path)
