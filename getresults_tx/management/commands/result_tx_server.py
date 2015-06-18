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
from getresults_tx.dispatcher import Dispatcher


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('hostname', nargs=1, type=str)
        parser.add_argument('source_dir', nargs=1, type=str)
        parser.add_argument('destination_dir', nargs=1, type=str)

    def handle(self, *args, **options):
        hostname = str(options['hostname'][0])
        source_dir = str(options['source_dir'][0])
        destination_dir = str(options['destination_dir'][0])
        server = Server(
            hostname=hostname,
            source_dir=source_dir,
            destination_dir=destination_dir,
            dispatcher=Dispatcher,
            mkdir=False)
        sys.stdout.write('Watching files in {}...\n'.format(source_dir))
        server.serve_forever()
