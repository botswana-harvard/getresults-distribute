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
import pwd
import pytz
import random
import shutil
import socket
import string
import time

from builtins import IsADirectoryError, FileNotFoundError, ConnectionRefusedError, ConnectionResetError
from datetime import datetime
from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException
from scp import SCPClient, SCPException
from watchdog.events import PatternMatchingEventHandler

from django.conf import settings
from django.utils import timezone

from .file_handlers import BaseFileHandler
from .folder_handlers import BaseLookupFolderHandler, BaseFolderHandler
from .models import TX_SENT, History

tz = pytz.timezone(settings.TIME_ZONE)


class OverrideMethodError(Exception):
    pass


class EventHandlerError(Exception):
    pass


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)


class BaseEventHandler(PatternMatchingEventHandler):
    """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
    """
    def __init__(self, hostname=None, remote_user=None, trusted_host=None):
        super(BaseEventHandler, self).__init__(ignore_directories=True)
        self.hostname = hostname or 'localhost'
        self.remote_user = remote_user or pwd.getpwuid(os.getuid()).pw_name
        self.trusted_host = True if (trusted_host or self.hostname == 'localhost') else False

    def process(self, event):
        print('{} {} {} Not handled.'.format(timezone.now(), event.event_type, event.src_path))

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)


class FolderEventHandler(BaseEventHandler):
    """An event handler that moves a file from a source folder to a destination folder.

    :func:`on_created` and on :func:`on_modified` and handled.
    """
    folder_handler = BaseFolderHandler()
    patterns = ['*.*']

    def __init__(
            self, file_handler=None, source_dir=None, destination_dir=None, archive_dir=None,
            mkdir_local=None, mkdir_destination=None, mime_types=None, file_patterns=None,
            touch_existing=None, file_mode=None, **kwargs):
        """
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

        :param mkdir_destination: if True will attempt to create the remote folder or folders.
                             See also model RemoteFolder. (Default: False)
        :type mkdir_destination: boolean
        """

        super(FolderEventHandler, self).__init__(**kwargs)
        self.mkdir_local = mkdir_local
        self.mkdir_destination = mkdir_destination
        self.check_folders(source_dir, archive_dir, destination_dir)
        self.touch_existing = touch_existing
        if touch_existing:
            self.update_file_mode(file_mode)
        try:
            self.file_handler = file_handler(**kwargs)
        except TypeError as e:
            if 'object is not callable' in str(e):
                self.file_handler = BaseFileHandler(**kwargs)
            else:
                raise
        self.filename_max_length = 50
        try:
            self.mime_types = [s.encode() for s in mime_types]
        except TypeError:
            raise EventHandlerError('No mime_types defined. Nothing to do. Got {}'.format(mime_types))
        try:
            self.file_patterns = [str(s) for s in file_patterns]
        except TypeError:
            raise EventHandlerError('No patterns defined. Nothing to do. Got {}'.format(file_patterns))

    def on_created(self, event):
        self.process_on_added(event)

    def on_modified(self, event):
        if os.path.exists(event.src_path):
            self.process_on_added(event)

    def process_on_added(self, event):
        """Moves file from source_dir to the destination_dir as
        determined by :func:`folder_handler.select`."""
        print('{} {} {}'.format(timezone.now(), event.event_type, event.src_path))
        filename = event.src_path.split('/')[-1:][0]
        path = os.path.join(self.source_dir, filename)
        mime_type = magic.from_file(path, mime=True)
        if mime_type in self.mime_types:
            folder_selection = self.folder_handler.select(self, filename, mime_type, self.destination_dir)
            if not folder_selection.path:
                print('Copy failed. Unable to \'select\' remote folder for {}'.format(filename))
                return None
            else:
                fileinfo = self.copy_to_folder(filename, folder_selection.path)
                if fileinfo:
                    path = os.path.join(self.source_dir, filename)
                    if self.archive_dir:
                        fileinfo['archive_filename'] = self.archive_filename(filename)
                        self.update_history(fileinfo, TX_SENT, folder_selection, mime_type)
                        os.rename(path, os.path.join(self.archive_dir, fileinfo['archive_filename']))
                    else:
                        os.remove(path)

    def check_folders(self, source_dir, archive_dir, destination_dir):
        """Check that folders exist and create if mkdir is True."""
        self.source_dir = self.check_local_path(source_dir)
        self.archive_dir = self.check_local_path(archive_dir)
        self.destination_dir = self.check_destination_path(destination_dir)

    def copy_to_folder(self, filename, destination_dir):
        """Copies file to the destination path and
        archives if the archive_dir has been specified."""
        source_filename = os.path.join(self.source_dir, filename)
        destination_filename = os.path.join(destination_dir, filename)
        if not os.path.isfile(source_filename):
            return None
        fileinfo = self.statinfo(self.source_dir, filename)
        try:
            shutil.copy2(source_filename, destination_filename)
        except IsADirectoryError:
            fileinfo = None
        return fileinfo

    def check_local_path(self, path):
        """Returns the path or raises an Exception if path does not exist locally."""
        path = os.path.expanduser(path)
        path = path[:-1] if path.endswith('/') else path
        if not os.path.exists(path):
            if self.mkdir_local:
                os.makedirs(path)
            else:
                raise FileNotFoundError(path)
        return path

    def check_destination_path(self, path, mkdir_destination=None):
        """Returns the destination path after checking if it exists or making it (mkdir=True)."""
        if mkdir_destination or self.mkdir_destination:
            os.makedirs(path)
        else:
            raise FileNotFoundError('{} does not exist.'.format(path))
        return path

    def statinfo(self, path, filename):
        statinfo = os.stat(os.path.join(self.source_dir, filename))
        return {
            'path': path,
            'filename': filename,
            'size': statinfo.st_size,
            'timestamp': tz.localize(datetime.fromtimestamp(statinfo.st_mtime)),
        }

    def update_history(self, fileinfo, status, folder_selection, mime_type):
        history = History(
            hostname=socket.gethostname(),
            remote_hostname=self.hostname,
            path=self.source_dir,
            remote_path=folder_selection.path,
            remote_folder=folder_selection.name,
            remote_folder_tag=folder_selection.tag,
            archive_path=self.archive_dir,
            filename=fileinfo['filename'],
            filesize=fileinfo['size'],
            filetimestamp=fileinfo['timestamp'],
            mime_type=mime_type,
            status=status,
            sent_datetime=timezone.now(),
            user=self.remote_user,
        )
        history.archive.name = 'archive/{}'.format(fileinfo['archive_filename'])
        history.save()
        return history

    def archive_filename(self, filename):
        suffix = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(5))
        try:
            f, ext = filename.split('.')
        except ValueError:
            f, ext = filename, ''
        return '.'.join(['{}_{}'.format(f, suffix), ext])

    def touch_files(self):
        for filename in self.filtered_listdir(os.listdir(self.source_dir), self.source_dir):
            touch(os.path.join(self.source_dir, filename))

    def update_file_mode(self, mode):
        """Updates file mode of and touches existing files ."""
        mode = mode or 0o644
        for filename in self.filtered_listdir(os.listdir(self.source_dir), self.source_dir):
            if mode:
                os.chmod(os.path.join(self.source_dir, filename), mode)

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


class LocalFolderEventHandler(FolderEventHandler):

    folder_handler = BaseLookupFolderHandler()
    patterns = ['*.*']


class RemoteFolderEventHandler(FolderEventHandler):

    """A folder handler that scp's files to a remote folder.

    * copies file to destination
    * moves file to archive
    * updates sent history

    Attributes:
        folder_handler: You should create your own folder_handler by
                        subclassing the BaseLookupFolderHandler.
                        class. See module folder_handlers for examples.
        patterns:       a list of patterns such as ['*.pdf'].

    """
    folder_handler = BaseLookupFolderHandler()
    patterns = ['*.*']

    def __init__(self, timeout=None, **kwargs):
        self.timeout = timeout or 5.0
        self.ssh = None
        super(RemoteFolderEventHandler, self).__init__(**kwargs)

    def check_folders(self, source_dir, archive_dir, destination_dir):
        """Checks that all working folders, source, destination (on remote) and archive exist."""
        self.source_dir = self.check_local_path(source_dir)
        self.archive_dir = self.check_local_path(archive_dir)
        with SSHClient() as ssh:
            self.connect(ssh=ssh)
            self.destination_dir = self.check_destination_path(destination_dir, ssh=ssh)

    def connect(self, ssh=None):
        """Connects the ssh instance.

        If :param:`ssh` is not provided will connect `self.ssh`.
        """
        ssh = ssh if ssh else self.ssh
        ssh.load_system_host_keys()
        if self.trusted_host:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
        while True:
            try:
                ssh.connect(
                    self.hostname,
                    username=self.remote_user,
                    timeout=self.timeout,
                    compress=True,
                )
                print('Connected to host {}. '.format(self.hostname))
                break
            except (socket.timeout, ConnectionRefusedError) as e:
                print('{}. {} for {}@{}. Retrying ...'.format(
                    timezone.now(), str(e), self.remote_user, self.hostname)
                )
                time.sleep(5)
            except AuthenticationException as e:
                raise AuthenticationException(
                    'Got {} for user {}@{}'.format(
                        str(e)[0:-1], self.remote_user, self.hostname))
            except BadHostKeyException as e:
                raise BadHostKeyException(
                    'Add server to known_hosts on host {}.'
                    ' Got {}.'.format(e, self.hostname))
            except socket.gaierror:
                raise socket.gaierror('Hostname {} not known or not available'.format(self.hostname))
            except ConnectionResetError as e:
                raise ConnectionResetError('{} for {}@{}'.format(str(e), self.remote_user, self.hostname))
            except SSHException as e:
                raise SSHException('{} for {}@{}'.format(str(e), self.remote_user, self.hostname))

    def reconnect(self):
        self.connect()

    def copy_to_folder(self, filename, destination_dir):
        """Scp file to destination_dir on remote host.
        @param filename: file name without path
        @type filename: str
        @param destination_dir: remote host folder
        @type filename: str

        @return fileinfo dict"""
        with SCPClient(self.ssh.get_transport()) as scp_client:
            try:
                fileinfo = self.put(filename, destination_dir, scp_client)
            except SCPException as e:
                if 'No response from server' in str(e):
                    self.reconnect()
                    fileinfo = self.put(filename, destination_dir, scp_client)
                elif 'Permission denied' in str(e):
                    print('{}, skipping ...'.format(str(e)))
                    fileinfo = None  # skip
                else:
                    raise
        return fileinfo

    def put(self, filename, destination_dir, scp_client):
        """Copies file to the destination path and
        archives if the archive_dir has been specified.

        @param filename: file name without path
        @type filename: str
        @param destination_dir: remote host folder
        @type filename: str
        @param scp_client: instance of :class:`SCPClient`

        @return fileinfo dict"""

        source_filename = os.path.join(self.source_dir, filename)
        destination_filename = os.path.join(destination_dir, filename)
        if not os.path.isfile(source_filename):
            return None
        fileinfo = self.statinfo(self.source_dir, filename)
        try:
            scp_client.put(
                source_filename,
                destination_filename,
            )
        except IsADirectoryError:
            fileinfo = None
        return fileinfo

    def check_destination_path(self, path, mkdir_destination=None, ssh=None):
        """Returns the destination_dir or raises an Exception if destination_dir does
        not exist on the remote host.

        @param path: path on remote host
        @type path: byte or str
        @param mkdir_destination: if True attempts to create the remote folder.
        @type mkdir_destination: boolean

        @raise FileNotFoundError: if path does not exist and mkdir_destination is False

        @return path
        """
        ssh = ssh if ssh else self.ssh
        if path[0:1] == b'~' or path[0:1] == '~':
            _, stdout, _ = ssh.exec_command("pwd")
            path = os.path.join(stdout.readlines()[0].strip(), path.replace('~/', ''))
        with SFTPClient.from_transport(ssh.get_transport()) as sftp:
            try:
                sftp.chdir(path)
            except IOError:
                if mkdir_destination or self.mkdir_destination:
                    self.mkdir_p(sftp, path)
                else:
                    raise FileNotFoundError('{} not found on remote host.'.format(path))
            return path
        return None

    def mkdir_p(self, sftp, remote_directory):
        """Changes to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if self.mkdir_destination:
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
