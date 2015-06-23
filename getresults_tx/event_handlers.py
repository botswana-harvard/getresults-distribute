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
import pytz
import pwd
import random
import socket
import string

from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException
from scp import SCPClient
from watchdog.events import PatternMatchingEventHandler

from django.conf import settings
from django.utils import timezone

from .folder_handlers import FolderHandler
from .models import TX_SENT, History

tz = pytz.timezone(settings.TIME_ZONE)


class BaseEventHandler(PatternMatchingEventHandler):
    """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
    """
    def __init__(self, hostname, timeout, remote_user=None):
        self.hostname = hostname or 'localhost'
        self.timeout = timeout or 5.0
        try:
            self.remote_user = remote_user or settings.GRTX_REMOTE_USERNAME
        except AttributeError:
            self.remote_user = pwd.getpwuid(os.getuid()).pw_name
        super(BaseEventHandler, self).__init__(ignore_directories=True)

    def process(self, event):
        print('{} {}'.format(event.event_type, event.src_path))
        print('Nothing to do.')

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def _connect(self, ssh):
        try:
            ssh.connect(
                self.hostname,
                username=self.remote_user,
                timeout=self.timeout,
            )
        except SSHException:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(
                self.hostname,
                username=self.remote_user,
                timeout=self.timeout,
            )
        return ssh

    def connect(self):
        """Returns a connected ssh instance."""
        ssh = SSHClient()
        ssh.load_system_host_keys()
        try:
            return self._connect(ssh)
        except AuthenticationException as e:
            raise AuthenticationException(
                'Got {} for user {}@{}'.format(
                    str(e)[0:-1], self.remote_user, self.hostname))
        except BadHostKeyException as e:
            raise BadHostKeyException(
                'Add server to known_hosts on host {}.'
                ' Got {}.'.format(e, self.hostname))
        except socket.timeout:
            print('Cannot connect to host {}.'.format(self.hostname))
            return None


class RemoteFolderEventHandler(BaseEventHandler):

    folder_handler = FolderHandler()
    patterns = ['*.*']

    def on_created(self, event):
        self.process_added(event)

    def on_modified(self, event):
        if os.path.exists(event.src_path):
            self.process_added(event)

    def process_added(self, event):
        print('{} {}'.format(event.event_type, event.src_path))
        ssh = self.connect()
        filename = event.src_path.split('/')[-1:][0]
        path = os.path.join(self.source_dir, filename)
        mime_type = magic.from_file(path, mime=True)
        if mime_type in self.mime_types:
            folder_selection = self.select_destination_dir(filename, mime_type)
            if not folder_selection.path:
                return None
            else:
                with SCPClient(ssh.get_transport()) as scp:
                    fileinfo = self.put(scp, filename, folder_selection.path)
                if fileinfo:
                    if self.archive_dir:
                        fileinfo['archive_filename'] = self.archive_filename(filename)
                        self.update_history(fileinfo, TX_SENT, folder_selection, mime_type)
                        os.rename(path, os.path.join(self.archive_dir, fileinfo['archive_filename']))
                    else:
                        os.remove(path)

    def select_destination_dir(self, filename, mime_type):
        """Returns the full path of the destination folder.

        Return value can be a list or tuple as long as the first item
        is the destination_dir."""
        try:
            return self.folder_handler.select(self, filename, mime_type, self.destination_dir)
        except TypeError as e:
            if 'object is not callable' in str(e):
                return self.destination_dir, None, None
            else:
                raise

    def put(self, scp, filename, destination_dir):
        """Copies file to the destination path and
        archives if the archive_dir has been specified."""

        source_filename = os.path.join(self.source_dir, filename)
        destination_filename = os.path.join(destination_dir, filename)
        if not os.path.isfile(source_filename):
            return None
        fileinfo = self.statinfo(self.source_dir, filename)
        try:
            scp.put(
                source_filename,
                destination_filename,
                username=self.remote_user,
            )
        except IsADirectoryError:
            fileinfo = None
        return fileinfo

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
            remote_folder_hint=folder_selection.hint,
            archive_path=self.archive_dir,
            filename=fileinfo['filename'],
            filesize=fileinfo['size'],
            filetimestamp=fileinfo['timestamp'],
            mime_type=mime_type,
            status=status,
            sent_datetime=timezone.now(),
            user=self.remote_user,
        )
        if self.archive_dir:
            history.archive.name = 'archive/{}'.format(fileinfo['archive_filename'])
        history.save()

    def archive_filename(self, filename):
        suffix = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(5))
        try:
            f, ext = filename.split('.')
        except ValueError:
            f, ext = filename, ''
        return '.'.join(['{}_{}'.format(f, suffix), ext])
