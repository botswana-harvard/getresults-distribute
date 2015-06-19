# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import magic
import os
import time

from paramiko import SFTPClient

from .event_handlers import BaseEventHandler


class Server(BaseEventHandler):

    def __init__(self, event_handler, hostname=None, timeout=None,
                 source_dir=None, destination_dir=None, archive_dir=None,
                 file_prefix=None, file_suffix=None, mime_types=None, exclude_existing_files=None,
                 mkdir_local=None, mkdir_remote=None, **kwargs):
        """
        :param event_handler: Custom event handler for added and removed files. If omitted the
                              :class:`BaseEventHandler` will be used by default.

        :param file_prefix: used in filtering the files to process. (Default: None)
        :type file_prefix: str

        :param file_suffix: used in filtering the files to process. (Default: None)
        :type file_suffix: str

        :param mime_type: comma separated list of mime_types. (Default: 'text/plain').
        :type mime_type: str

        :param mkdir_remote: if True will attempt to create the remote folder or folders.
                             See also model RemoteFolder. (Default: False)
        :type mkdir_remote: boolean
        """
        super(Server, self).__init__(hostname, timeout)
        self.event_handler = event_handler(hostname, timeout, **kwargs) or BaseEventHandler(hostname, timeout)
        self.hostname = hostname or 'localhost'
        self.port = 22
        self.timeout = timeout or 5.0
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
        try:
            self.mime_types = [s.encode() for s in mime_types.split(',')]
        except AttributeError:
            self.mime_types = [b'text/plain']
        self.mkdir_remote = mkdir_remote
        self.mkdir_local = mkdir_local
        self.exclude_existing_files = exclude_existing_files
        self.source_dir = self.local_folder(source_dir, update_permissions=True)
        self.destination_dir = self.remote_folder(destination_dir)
        if archive_dir:
            self.archive_dir = self.local_folder(archive_dir)
        else:
            self.archive_dir = None
        event_handler = self._wrapper(event_handler)

    def _wrapper(self, event_handler):
        event_handler.source_dir = self.source_dir
        event_handler.destination_dir = self.destination_dir
        event_handler.archive_dir = self.archive_dir
        event_handler.remote_folder = self.remote_folder
        event_handler.mkdir_remote = self.mkdir_remote
        return event_handler

    def watch(self, die=None, sleep=None):
        """Watches the source_dir for new files and copies them to the destination_dir.

        :param sleep: integer for timer. (Default: 5)

        :param die: if True allows 2 loops then breaks. 2 loops means both
                    handlers on_added and on_removed will be called. (Default: False)
        :type die: boolean

        For example:
            >>> server = Server(
                    EventHandler,
                    hostname='localhost',
                    source_dir=<source_dir>,
                    destination_dir=<destination_dir>,
                    file_suffix='txt'
                    mime_type='application/pdf'
                )
            >>> server.watch()
        """
        before = self.before()
        n = 0
        while n >= 0:
            time.sleep(sleep or 5)
            before = self.watch_once(before)
            if die:
                n += 1
                if n == 2:
                    break

    def watch_once(self, before):
        """Moves files in source_dir to destination_dir.

        Returns the "after" list which is a list of filenames currently in source_dir.

        Calls on_added and on_removed handlers."""
        after = []
        for f in os.listdir(self.source_dir):
            after.append(f)
        after = self.filter_by_filetype(after)
        added = [f for f in after if f not in before]
        removed = [f for f in before if f not in after]
        if added:
            self.event_handler.on_added(added)
        if removed:
            self.event_handler.on_removed(removed)
        return after

    def before(self):
        """Returns a list of files in the source_dir before the watch loop begins."""
        before = []
        if self.exclude_existing_files:
            for f in os.listdir(self.source_dir):
                if os.path.isfile(os.path.join(self.source_dir, f)):
                    before.append(f)
        before = self.filter_by_filetype(before)
        return before

    def local_folder(self, path, update_permissions=None):
        """Returns the path or raises an Exception if path does not exist."""
        path = os.path.expanduser(path)
        path = path[:-1] if path.endswith('/') else path
        if not os.path.exists(path):
            if self.mkdir_local:
                os.makedirs(path)
            else:
                raise FileNotFoundError(path)
        if update_permissions:
            for filename in self.filter_by_filetype(os.listdir(path), path):
                os.chmod(os.path.join(path, filename), 0o777)
        return path

    def remote_folder(self, path, mkdir_remote=None):
        """Returns the path or raises an Exception if path does not exist on the remote host."""
        path = os.path.expanduser(path)
        path = path[:-1] if path.endswith('/') else path
        ssh = self.connect()
        with SFTPClient.from_transport(ssh.get_transport()) as sftp:
            try:
                sftp.chdir(path)
            except IOError:
                if mkdir_remote or self.mkdir_remote:
                    self.mkdir_p(sftp, path)
                else:
                    raise FileNotFoundError('{} not found on remote host.'.format(path))
        return path

    def filter_by_filetype(self, listdir, basedir=None):
        """Returns listdir as is or filtered by prefix and/or suffix and mime_type."""
        basedir = basedir or self.source_dir
        lst = []
        for f in listdir:
            if (magic.from_file(os.path.join(basedir, f), mime=True) in self.mime_types and
                    f.startswith(self.file_prefix or '') and
                    f.endswith(self.file_suffix or '')):
                lst.append(f)
        return lst

    def mkdir_p(self, sftp, remote_directory):
        """Changes to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if self.mkdir_remote:
            if remote_directory == '/':
                # absolute path so change directory to root
                sftp.chdir('/')
                return
            if remote_directory == '':
                # top-level relative directory must exist
                return
            try:
                sftp.chdir(remote_directory)  # sub-directory exists
            except IOError:
                dirname, basename = os.path.split(remote_directory.rstrip('/'))
                self.mkdir_p(sftp, dirname)  # make parent directories
                sftp.mkdir(basename)  # sub-directory missing, so created it
                sftp.chdir(basename)
                return True
