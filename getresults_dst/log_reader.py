# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys

from django.utils import timezone
from paramiko import SFTPClient, SSHClient

from .line_readers import BaseLineReader
from .models import LogReaderHistory
from .mixins import SSHConnectMixin


class LogReader (SSHConnectMixin):

    def __init__(self, line_reader, hostname, user, path, timeout=None):
        self.hostname = hostname or 'localhost'
        self.timeout = timeout or 5.0
        self.remote_user = user
        self.line_reader = line_reader() or BaseLineReader()
        self.path = path
        self.trusted_host = True
        self.filestat = None
        self.exception_count = 0
        self.match_count = 0

    def read(self, lastpos=None):
        line_number = 0
        if not lastpos:
            lastpos = self.get_lastpos()
        log_reader_history = self.update_history(lastpos)
        try:
            with SSHClient() as self.ssh:
                self.connect()
                lastpos = lastpos or 0
                with SFTPClient.from_transport(self.ssh.get_transport()) as sftp:
                    self.filestat = sftp.stat(self.path)
                    sys.stdout.write('Reading log {}@{}:{}\n\n'.format(
                        self.remote_user, self.hostname, self.path))
                    sys.stdout.write('Lastpos={}.\n'.format(lastpos))
                    sys.stdout.flush()
                    if lastpos == sftp.stat(self.path).st_size:
                        sys.stdout.write('No changes since last read.\n')
                        sys.stdout.write('Done.\n')
                        return None
                    with sftp.open(self.path) as f:
                        f.seek(lastpos)
                        for line_number, line in enumerate(f):
                            self.line_reader.on_newline(line, lastpos, line_number, log_reader_history)
                            lastpos = f.tell()
        except KeyboardInterrupt:
            sys.stdout.write('Stopped at {} for {}@{}:{}\n'.format(
                lastpos, self.remote_user, self.hostname, self.path))
            sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
        log_reader_history.lastpos = lastpos
        log_reader_history.lines = line_number
        log_reader_history.ended = timezone.now()
        log_reader_history.save()
        sys.stdout.write('Done. Lastpos={}.\nSee LogReaderHistory id={}.\n'.format(
            lastpos, log_reader_history.id))
        sys.stdout.flush()
        return lastpos

    def update_history(self, lastpos):
        return LogReaderHistory.objects.create(lastpos=lastpos or 0)

    def get_lastpos(self):
        try:
            return LogReaderHistory.objects.all().order_by('-started')[0].lastpos
        except IndexError:
            return 0
