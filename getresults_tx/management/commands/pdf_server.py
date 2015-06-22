# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys

from django.core.management.base import BaseCommand

from getresults_tx.server import Server
from getresults_tx.event_handlers import RemoteFolderEventHandler


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('hostname', nargs=1, type=str)
        parser.add_argument('source_dir', nargs=1, type=str)
        parser.add_argument('destination_dir', nargs=1, type=str)
        parser.add_argument('archive_dir', nargs=1, type=str)

    def handle(self, *args, **options):
        hostname = str(options['hostname'][0])
        source_dir = str(options['source_dir'][0])
        destination_dir = str(options['destination_dir'][0])
        archive_dir = str(options['archive_dir'][0])
        server = Server(
            RemoteFolderEventHandler,
            hostname=hostname,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir=False)
        sys.stdout.write(str(Server))
        sys.stdout.write('Press CTRL-C to stop the observer.')
        server.observe()
