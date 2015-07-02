# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import socket
import sys

from builtins import ConnectionResetError, ConnectionRefusedError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from paramiko import SSHException

from getresults_dst.getresults import GrRemoteFolderEventHandler
from getresults_dst.server import Server


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        hostname = settings.GRTX_REMOTE_HOSTNAME
        remote_user = settings.GRTX_REMOTE_USERNAME
        source_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_UPLOAD_FOLDER)
        destination_dir = settings.GRTX_REMOTE_FOLDER
        archive_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_ARCHIVE_FOLDER)
        file_patterns = settings.GRTX_FILE_PATTERNS
        mime_types = settings.GRTX_MIME_TYPES

        event_handler = GrRemoteFolderEventHandler(
            hostname=hostname,
            remote_user=remote_user,
            trusted_host=True,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=file_patterns,
            mime_types=mime_types,
            touch_existing=True,
            mkdir_destination=True)

        try:
            server = Server(event_handler)
        except (ConnectionResetError, SSHException, ConnectionRefusedError, socket.gaierror) as e:
            raise CommandError(str(e))
        sys.stdout.write('\n' + str(server) + '\n')
        sys.stdout.write('File patterns: {}\n'.format(','.join([x for x in server.event_handler.file_patterns])))
        sys.stdout.write('Mime: {}\n'.format(','.join([x.decode() for x in server.event_handler.mime_types])))
        sys.stdout.write('Upload folder: {}\n'.format(server.event_handler.source_dir))
        sys.stdout.write(
            'Remote folder: {}@{}:{}\n'.format(
                server.event_handler.remote_user, server.event_handler.hostname, server.event_handler.destination_dir))
        sys.stdout.write('Archive folder: {}\n'.format(server.event_handler.archive_dir))
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
        server.observe()
