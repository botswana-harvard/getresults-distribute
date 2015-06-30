# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import time

from django.utils import timezone
from paramiko import SSHClient
from watchdog.observers import Observer

from .event_handlers import RemoteFolderEventHandler


class ServerError(Exception):
    pass


class Server(object):

    def __init__(self, event_handler):
#                  , file_handler=None, hostname=None, timeout=None, remote_user=None,
#                  source_dir=None, destination_dir=None, archive_dir=None,
#                  mime_types=None, file_patterns=None, file_mode=None, touch_existing=None,
#                  mkdir_local=None, mkdir_destination=None, trusted_host=None):
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

        :param mkdir_destination: if True will attempt to create the remote folder or folders.
                             See also model RemoteFolder. (Default: False)
        :type mkdir_destination: boolean
        """
        self.event_handler = event_handler
#         try:
#             self.event_handler = event_handler(
#                 hostname=hostname, remote_user=remote_user, file_handler=file_handler,
#                 timeout=timeout, mkdir_local=mkdir_local, mkdir_destination=mkdir_destination,
#                 source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir,
#                 mime_types=mime_types, file_patterns=file_patterns, file_mode=file_mode, trusted_host=trusted_host)
#         except TypeError as e:
#             if 'object is not callable' in str(e):
#                 self.event_handler = RemoteFolderEventHandler(
#                     hostname=hostname, remote_user=remote_user, file_handler=file_handler,
#                     timeout=timeout, mkdir_local=mkdir_local, mkdir_destination=mkdir_destination,
#                     source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir,
#                     mime_types=mime_types, file_patterns=file_patterns, file_mode=file_mode, trusted_host=trusted_host)
#             else:
#                 raise

    def __str__(self):
        return 'Server started on {}'.format(timezone.now())

    def observe(self, sleep=None):
        with SSHClient() as self.event_handler.ssh:
            observer = Observer()
            observer.schedule(self.event_handler, path=self.event_handler.source_dir)
            self.event_handler.connect()
            observer.start()
            try:
                while True:
                    time.sleep(sleep or 1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
