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

from django.utils import timezone
from paramiko import SFTPClient, SSHClient
from watchdog.observers import Observer

from .event_handlers import BaseEventHandler
from .file_handlers import BaseFileHandler


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)


class ServerError(Exception):
    pass


class Server(BaseEventHandler):

    def __init__(self, event_handler, hostname=None, timeout=None, remote_user=None,
                 source_dir=None, destination_dir=None, archive_dir=None,
                 mime_types=None, file_patterns=None, file_mode=None, touch_existing=None,
                 mkdir_local=None, mkdir_remote=None, file_handler=None,
                 trusted_host=None, **kwargs):
        """
        See management command :func:`start_observer` or tests for usage.

        :param event_handler: Custom event handler for added and removed files. If omitted the
                              :class:`BaseEventHandler` will be used by default.

        :param file_handler: Custom file handler. If omitted the :class:`BaseFileHandler`
                             will be used by default.

        :param remote_user: the remote user name on hostname to use when connecting. (Default: current user).
        :type remote_user: str

        :param hostname: the remote host to connect to. (Default: 'localhost').
        :type hostname: str

        :param mime_type: comma separated list of mime_types. (Default: 'text/plain').
        :type mime_type: str

        :param file_mode: updates existing files to this file mode. Existing files
                          are files in source_dir before starting the observer. (Default: 644)
        :type file_mode: integer

        :params file_patterns: a list of patterns, e.g. ['*.pdf']
        :type file_patterns: list or tuple

        :param touch_existing: if True will `touch` existing files to trigger an event
        :type touch_existing: boolean

        :param mkdir_remote: if True will attempt to create the remote folder or folders.
                             See also model RemoteFolder. (Default: False)
        :type mkdir_remote: boolean
        """
        super(Server, self).__init__(hostname, timeout, remote_user)
        self.event_handler = self._handler(
            event_handler, BaseEventHandler, hostname=hostname, timeout=timeout, remote_user=remote_user)
        self.file_handler = self._handler(file_handler, BaseFileHandler)
        self.filename_max_length = 50
        self.hostname = hostname or 'localhost'
        self.trusted_host = True if (trusted_host or self.hostname == 'localhost') else False
        self.port = 22
        self.timeout = timeout or 5.0
        try:
            self.mime_types = [s.encode() for s in mime_types]
        except TypeError:
            raise ServerError('No mime_types defined. Nothing to do. Got {}'.format(mime_types))
        try:
            self.file_patterns = [str(s) for s in file_patterns]
        except TypeError:
            raise ServerError('No patterns defined. Nothing to do. Got {}'.format(file_patterns))
        self.mkdir_remote = mkdir_remote
        self.mkdir_local = mkdir_local
        self.source_dir = self.local_folder(source_dir, update_permissions=True)
        with SSHClient() as self.ssh:
            self.connect()
            self.destination_dir = self.remote_folder(destination_dir)
        if archive_dir:
            self.archive_dir = self.local_folder(archive_dir)
        else:
            self.archive_dir = None
        event_handler = self._wrapper(event_handler)
        self.touch_existing = touch_existing
        if touch_existing:
            self.update_file_mode(file_mode)

    def __str__(self):
        return 'Server started on {}'.format(timezone.now())

    def _handler(self, handler, base_handler, **kwargs):
        try:
            return handler(**kwargs)
        except TypeError as e:
            if 'object is not callable' in str(e):
                return base_handler(**kwargs)
            else:
                raise

    def _wrapper(self, event_handler):
        event_handler.source_dir = self.source_dir
        event_handler.destination_dir = self.destination_dir
        event_handler.archive_dir = self.archive_dir
        event_handler.remote_folder = self.remote_folder
        event_handler.mkdir_remote = self.mkdir_remote
        event_handler.mime_types = self.mime_types
        event_handler.patterns = self.file_patterns
        return event_handler

    def observe(self, sleep=None):
        with SSHClient() as self.ssh:
            self.connect()
            self.event_handler.ssh = self.ssh
            observer = Observer()
            observer.schedule(self.event_handler, path=self.source_dir)
            observer.start()
            if self.touch_existing:
                self.touch_files()
            try:
                while True:
                    time.sleep(sleep or 1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()

    def touch_files(self):
        for filename in self.filtered_listdir(os.listdir(self.source_dir), self.source_dir):
            touch(os.path.join(self.source_dir, filename))

    def update_file_mode(self, mode):
        """Updates file mode of and touches existing files ."""
        mode = mode or 0o644
        for filename in self.filtered_listdir(os.listdir(self.source_dir), self.source_dir):
            if mode:
                os.chmod(os.path.join(self.source_dir, filename), mode)

    def local_folder(self, path, update_permissions=None):
        """Returns the path or raises an Exception if path does not exist."""
        path = os.path.expanduser(path)
        path = path[:-1] if path.endswith('/') else path
        if not os.path.exists(path):
            if self.mkdir_local:
                os.makedirs(path)
            else:
                raise FileNotFoundError(path)
        return path

    def remote_folder(self, path, mkdir_remote=None):
        """Returns the path or raises an Exception if path does not exist on the remote host."""
        remote_path = None
        if path[0:1] == b'~' or path[0:1] == '~':
            _, stdout, _ = self.ssh.exec_command("pwd")
            remote_path = os.path.join(stdout.readlines()[0].strip(), path.replace('~/', ''))
        else:
            remote_path = path
        with SFTPClient.from_transport(self.ssh.get_transport()) as sftp:
            try:
                sftp.chdir(remote_path)
            except IOError:
                if mkdir_remote or self.mkdir_remote:
                    self.mkdir_p(sftp, remote_path)
                else:
                    raise FileNotFoundError('{} not found on remote host.'.format(remote_path))
        return remote_path

    def filtered_listdir(self, listdir, basedir=None):
        """Returns listdir as is or filtered by patterns and mime_type and length of filename."""
        basedir = basedir or self.source_dir
        lst = []
        for f in listdir:
            mime_type = magic.from_file(os.path.join(basedir, f), mime=True)
            if (mime_type in self.mime_types and
                    [pat for pat in self.file_patterns if f.endswith(pat.split('*')[1])] and
                    len(f) <= self.filename_max_length):
                if self.file_handler.process(f, basedir, mime_type):
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
