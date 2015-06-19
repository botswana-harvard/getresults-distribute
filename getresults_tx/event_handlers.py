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
import socket

from datetime import datetime
from paramiko import SSHClient
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException
from scp import SCPClient

from django.conf import settings
from django.utils import timezone

from .models import RemoteFolder, TX_SENT, History

tz = pytz.timezone(settings.TIME_ZONE)


class BaseEventHandler(object):

    def __init__(self, hostname, timeout):
        self.hostname = hostname or 'localhost'
        self.timeout = timeout or 5.0
        self.user = pwd.getpwuid(os.getuid()).pw_name

    def on_added(self, added):
        """Override for your needs.

        :param added: list of file names added to source_dir
        """
        pass

    def on_removed(self, removed):
        """Override for your needs.

        :param removed: list of file names removed from source_dir
                        and put in the destination_dir
        """
        pass

    def connect(self):
        """Returns an ssh instance."""
        ssh = SSHClient()
        ssh.load_system_host_keys()
        try:
            ssh.connect(
                self.hostname,
                timeout=self.timeout
            )
        except AuthenticationException as e:
            raise AuthenticationException(
                'Got {}. Add user {} to authorized_keys on host {}'.format(
                    e, self.user, self.hostname))
        except BadHostKeyException as e:
            raise BadHostKeyException(
                'Add server to known_hosts on host {}.'
                ' Got {}.'.format(e, self.hostname))
        return ssh


class RemoteFolderEventHandler(BaseEventHandler):

    custom_select_destination_func = None

    def __init__(self, hostname, timeout, remote_folder_callback=None):
        super(RemoteFolderEventHandler, self).__init__(hostname, timeout)
        self._destination_subdirs = {}

    def on_added(self, added):
        """Move added files to a remote host."""
        print('Added: {}'.format(', '.join(added)))
        ssh = self.connect()
        with SCPClient(ssh.get_transport()) as scp:
            for filename in added:
                path = os.path.join(self.source_dir, filename)
                mime_type = magic.from_file(path, mime=True)
                fileinfo, destination_dir = self.put(scp, filename)
                if fileinfo:
                    os.remove(path)
                    self.update_history(fileinfo, TX_SENT, destination_dir, mime_type)

    def on_removed(self, removed):
        print('Removed: {}'.format(', '.join(removed)))

    def select_destination_dir(self, filename):
        """Returns the full path of the destination folder."""
        try:
            return self.custom_select_destination_func(
                filename, self.destination_dir, self.remote_folder, self.mkdir_remote)
        except TypeError:
            return self.destination_dir

    @property
    def destination_subdirs(self):
        """Returns a dictionary of subfolders expected to exist in the destination_dir."""
        if not self._destination_subdirs.get(self.destination_dir):
            self._destination_subdirs = {self.destination_dir: {}}
            for remote_folder in RemoteFolder.objects.filter(base_path=self.destination_dir):
                fldr = self.remote_folder(self.destination_dir, remote_folder.folder)
                self._remote_subfolders[self.destination_dir].update({
                    remote_folder.name: fldr,
                    remote_folder.file_hint: fldr})
        return self._destination_subdirs

    def destination_subdir(self, key):
        """Returns the name of a destination_dir subfolder given a key.

        Key can be the folder name or the folder hint. See RemoteFolder model.
        """
        try:
            return self.destination_subdirs[key]
        except KeyError:
            return self.destination_dir

    def put(self, scp, filename, destination=None):
        """Copies file to the destination path and
        archives if the archive_dir has been specified."""

        destination_dir = self.select_destination_dir(filename)
        source_filename = os.path.join(self.source_dir, filename)
        destination_filename = os.path.join(destination_dir, filename)
        if not os.path.isfile(source_filename):
            return None
        fileinfo = self.statinfo(self.source_dir, filename)
        try:
            scp.put(
                source_filename,
                destination_filename
            )
            if self.archive_dir:
                scp.put(
                    source_filename,
                    destination_filename
                )
        except IsADirectoryError:
            fileinfo = None
        return fileinfo, destination_dir

    def statinfo(self, path, filename):
        statinfo = os.stat(os.path.join(self.source_dir, filename))
        return {
            'path': path,
            'filename': filename,
            'size': statinfo.st_size,
            'timestamp': tz.localize(datetime.fromtimestamp(statinfo.st_mtime)),
        }

    def update_history(self, fileinfo, status, destination_dir, mime_type, folder_hint=None):
        return History.objects.create(
            hostname=socket.gethostname(),
            remote_hostname=self.hostname,
            path=self.source_dir,
            remote_path=self.destination_dir,
            remote_folder=destination_dir or self.destination_dir,
            remote_folder_hint=folder_hint,
            archive_path=self.archive_dir,
            filename=fileinfo['filename'],
            filesize=fileinfo['size'],
            filetimestamp=fileinfo['timestamp'],
            mime_type=mime_type,
            status=status,
            sent_datetime=timezone.now(),
            user=self.user,
        )
