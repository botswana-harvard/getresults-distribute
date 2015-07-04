# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from getresults_dst.getresults import GrLogLineReader
from getresults_dst.log_reader import LogReader


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):

        hostname = settings.GRTX_REMOTE_HOSTNAME
        user = settings.GRTX_REMOTE_USERNAME
        logfile = settings.GRTX_REMOTE_LOGFILE
        reader = LogReader(GrLogLineReader, hostname, user, logfile)
        try:
            reader.read()
        except Exception as e:
            raise CommandError(str(e))
