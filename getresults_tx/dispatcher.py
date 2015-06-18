# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import pytz
import socket

from datetime import datetime
from scp import SCPClient

from django.conf import settings
from django.utils import timezone

from .models import History, RemoteFolder, TX_SENT
from .server import BaseDispatcher

tz = pytz.timezone(settings.TIME_ZONE)


class Dispatcher(BaseDispatcher):

    def __init__(self, *args):
        super(Dispatcher, self).__init__(*args)
        self._destination_subdirs = {}

    def on_added(self, added):
        print('Added: {}'.format(', '.join(added)))
        ssh = self.connect()
        with SCPClient(ssh.get_transport()) as scp:
            for filename in added:
                fileinfo = self.put(scp, filename)
                if fileinfo:
                    os.remove(os.path.join(self.source_dir, filename))
                    self.update_history(fileinfo, TX_SENT)

    def on_removed(self, removed):
        print('Removed: {}'.format(', '.join(removed)))

    def folder_hint(self, filename):
        return filename[0:6]

    @property
    def destination_subdirs(self):
        if not self._destination_subdirs.get(self.destination_dir):
            self._destination_subdirs = {self.destination_dir: {}}
            for remote_folder in RemoteFolder.objects.filter(base_path=self.destination_dir):
                fldr = self.remote_folder(self.destination_dir, remote_folder.folder)
                self._remote_subfolders[self.destination_dir].update({
                    remote_folder.name: fldr,
                    remote_folder.file_hint: fldr})
        return self._destination_subdirs

    def destination_subdir(self, key):
        try:
            return self.destination_subdirs[key]
        except KeyError:
            return self.destination_dir

    def put(self, scp, filename, destination=None):
        """Copies file to the destination path and
        archives if the archive_dir has been specified."""
        destination_dir = self.destination_subdir(self.folder_hint(filename))
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
        return fileinfo

    def statinfo(self, path, filename):
        statinfo = os.stat(os.path.join(self.source_dir, filename))
        return {
            'path': path,
            'filename': filename,
            'size': statinfo.st_size,
            'timestamp': tz.localize(datetime.fromtimestamp(statinfo.st_mtime)),
        }

    def update_history(self, fileinfo, status):
        return History.objects.create(
            hostname=socket.gethostname(),
            remote_hostname=self.hostname,
            path=self.source_dir,
            remote_path=self.destination_dir,
            archive_path=self.archive_dir,
            filename=fileinfo['filename'],
            filesize=fileinfo['size'],
            filetimestamp=fileinfo['timestamp'],
            status=status,
            sent_datetime=timezone.now(),
            user=self.user,
        )
