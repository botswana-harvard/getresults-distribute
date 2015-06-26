# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import pytz
import re
import sys

from apache_log_parser import make_parser, LineDoesntMatchException
from dateutil.parser import parse
from django.conf import settings
from getresults_dst.models import Acknowledgment, History

tz = pytz.timezone(settings.TIME_ZONE)


class BaseLineReader(object):

    def read(self, ln, *args):
        sys.stdout.write('\r{} ...'.format(ln[0:50]))


class RegexApacheLineReader(object):

    line_parser = make_parser('%a %b %B %t %m %q %H %X %P %r %R')
    pattern = re.compile(r'066\-[0-9]{8}\-[0-9]{1}[\_\-A-za-z0-9]{0,50}\.pdf')

    def __init__(self):
        self.match_count = 0
        self.exception_count = 0

    def read(self, ln, lastpos, line_number, log_reader_history):
        remote_ip, match_string, time_received = None, None, None
        try:
            values = self.line_parser(ln)
            remote_ip = values.get('remote_ip', '')
            time_received = values.get('time_received', None)
            match = re.search(self.pattern, values.get('query_string', ''))
            if match:
                match_string = match.group()
                self.match_count += 1
        except LineDoesntMatchException:
            self.exception_count += 1
            pass
        if match_string:
            time_received = time_received.replace('[', '').replace(']', '').replace('/', ' ')
            time_received = time_received[0:11] + ' ' + time_received[12:]
            time_received = parse(time_received)
            self.update_ack_history(ln, remote_ip, match_string, time_received)
        sys.stdout.write("\rbytes: {}    lines: {}    matches: {}    exceptions: {}".format(
            lastpos, line_number, self.match_count, self.exception_count))
        sys.stdout.flush()
        log_reader_history.matches = self.match_count
        log_reader_history.exceptions = self.exception_count
        return log_reader_history

    def update_ack_history(self, ln, remote_ip, match_string, time_received):
        try:
            history = History.objects.get(
                filename=match_string,
                ack_datetime__isnull=True,
                ack_user__isnull=True,
            )
            history.ack_datetime = time_received
            history.ack_user = remote_ip
            history.acknowledged = True
            history.save()
        except History.DoesNotExist:
            history = None
        acknowledgement = Acknowledgment.objects.create(
            filename=match_string,
            ack_user=remote_ip,
            ack_datetime=time_received,
            ack_string=ln[0:500],
            in_sent_history=True if history else False,
        )
        return acknowledgement
