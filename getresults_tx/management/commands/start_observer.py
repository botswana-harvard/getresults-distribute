# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from paramiko import SSHException

from getresults_tx.server import Server
from getresults_tx.event_handlers import RemoteFolderEventHandler


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        hostname = settings.GRTX_REMOTE_HOSTNAME
        source_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_UPLOAD_FOLDER)
        destination_dir = settings.GRTX_REMOTE_FOLDER
        archive_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_ARCHIVE_FOLDER)
        file_patterns = settings.GRTX_FILE_PATTERNS
        mime_types = settings.GRTX_MIME_TYPES
        try:
            server = Server(
                RemoteFolderEventHandler,
                hostname=hostname,
                source_dir=source_dir,
                destination_dir=destination_dir,
                archive_dir=archive_dir,
                file_patterns=file_patterns,
                mime_types=mime_types,
                touch_existing=True,
                mkdir_remote=True)
        except (ConnectionResetError, SSHException) as e:
            raise CommandError(str(e))
        sys.stdout.write('\n' + str(server) + '\n')
        sys.stdout.write('patterns: {}\n'.format(','.join([x for x in server.file_patterns])))
        sys.stdout.write('mime: {}\n'.format(','.join([x.decode() for x in server.mime_types])))
        sys.stdout.write('Upload folder: {}\n'.format(server.source_dir))
        sys.stdout.write(
            'Remote folder: {}@{}:{}\n'.format(server.remote_user, server.hostname, server.destination_dir))
        sys.stdout.write('Archive folder: {}\n'.format(server.archive_dir))
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
        server.observe()
