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
from django.core.exceptions import MultipleObjectsReturned

tz = pytz.timezone(settings.TIME_ZONE)


class BaseLineReader(object):

    def read(self, ln, lastpos, line_number, log_reader_history):
        """Read the line into the values dictionary and call on_match if there is a match."""
        self.on_newline(ln)
        sys.stdout.write("\rbytes: {}    lines: {}    matches: {}    exceptions: {}".format(
            lastpos, line_number, self.match_count, self.exception_count))
        sys.stdout.flush()
        log_reader_history.matches = self.match_count
        log_reader_history.exceptions = self.exception_count
        return log_reader_history

    def on_newline(self, ln):
        """Called for each new line"""
        pass


class RegexApacheLineReader(object):
    """ A line reader class that parses a line from an Apache2 access.log file.

    You will need to customize the line_parser, pattern and search_field.

    line_parser and pattern work together. In the default case, the pattern is
    applied to the \'query_string\' item in the dictionary returned by the line_parser.
    """

    line_parser = make_parser('%a %b %B %t %m %q %H %X %P %r %R')
    pattern = re.compile(r'\.pdf')
    search_field = 'query_string'

    def __init__(self):
        self.match_count = 0
        self.exception_count = 0

    def on_newline(self, ln):
        """Calls match and updates a match as an acknowledgement."""
        match_string, ln, remote_ip, time_received = self.match(ln)
        if match_string:
            self.update_ack_history(ln, remote_ip, match_string, time_received)

    def match(self, ln):
        """Matches the pattern to the relevant parsed item value and
        returns a tuple of values for the on_match event."""
        match_string, remote_ip, time_received = None, None, None
        try:
            values = self.line_parser(ln)
            remote_ip = values.get('remote_ip', '')
            time_received = values.get('time_received', None)
            match = re.search(self.pattern, values.get(self.search_field, ''))
            if match:
                match_string = match.group()
                self.match_count += 1
        except LineDoesntMatchException:
            self.exception_count += 1
            pass
        return match_string, ln, remote_ip, time_received

    def update_ack_history(self, ln, remote_ip, match_string, time_received):
        time_received = time_received.replace('[', '').replace(']', '').replace('/', ' ')
        time_received = time_received[0:11] + ' ' + time_received[12:]
        time_received = parse(time_received)
        try:
            history = History.objects.get(
                filename=match_string,
                ack_datetime__isnull=True,
                ack_user__isnull=True,
                acknowledged=False,
            )
            history.ack_datetime = time_received
            history.ack_user = remote_ip
            history.acknowledged = True
            history.save()
        except History.DoesNotExist:
            history = None
        except MultipleObjectsReturned:
            for history in History.objects.filter(
                    filename=match_string,
                    ack_datetime__isnull=True,
                    ack_user__isnull=True,
                    acknowledged=False):
                history.ack_datetime = time_received
                history.ack_user = remote_ip
                history.acknowledged = True
                history.save()
        acknowledgement = Acknowledgment.objects.create(
            filename=match_string,
            ack_user=remote_ip,
            ack_datetime=time_received,
            ack_string=ln[0:500],
            in_sent_history=True if history else False,
        )
        return acknowledgement
