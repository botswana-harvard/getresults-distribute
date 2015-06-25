import os
import re
import time
import sys

from builtins import FileNotFoundError

from apache_log_parser import make_parser, LineDoesntMatchException

from django.utils import timezone
from paramiko import SFTPClient, SSHClient

from .event_handlers import BaseEventHandler


class LineHandler(object):

    line_parser = make_parser('%a %b %B %t %m %q %H %X %P %r %R')
    pattern = re.compile(r'066\-[0-9]{8}\-[0-9]{1}')

    def process(self, ln):
        remote_ip, match_string, time_received = None, None, None
        exception = False
        try:
            values = self.line_parser(ln)
            remote_ip = values.get('remote_ip', '')
            time_received = values.get('time_received', None)
#             if values.get('remote_ip') == '154.70.150.42':
#                 print(values)
#                 print(' ')
#                 print(ln)
#                 print(' ')
#                 print(' ')
            match = re.search(self.pattern, values.get('query_string', ''))
            if match:
                self.match_count += 1
                match_string = match.group()
        except LineDoesntMatchException:
            exception = True
            pass
        if match_string:
            print('\n{}, {}, {}\n'.format(remote_ip, match_string, time_received))
        return (1 if match_string else 0, 1 if exception else 0)


class LogReader (BaseEventHandler):

    def __init__(self, line_handler, hostname, user, path, timeout=None):
        super(LogReader, self).__init__(hostname, timeout, remote_user=user)
        self.lastpos = None
        self.line_handler = line_handler()
        self.path = path
        self.trusted_host = True
        self.filestat = None
        self.exception_count = 0
        self.match_count = 0

    def read(self, lastpos=None):
        try:
            with SSHClient() as self.ssh:
                self.connect()
                self.lastpos = lastpos or 0
                with SFTPClient.from_transport(self.ssh.get_transport()) as sftp:
                    print('Begin reading {}@{}:{}'.format(self.remote_user, self.hostname, self.path))
                    self.filestat = sftp.stat(self.path)
                    if self.lastpos == sftp.stat(self.path):
                        return None
                    with sftp.open(self.path) as f:
                        f.seek(self.lastpos)
                        for index, line in enumerate(f):
                            (mcnt, ecnt) = self.line_handler.process(line)
                            self.match_count += mcnt
                            self.exception_count += ecnt
                            self.lastpos = f.tell()
                            sys.stdout.write("\rbytes: {}    lines: {}    matches: {}    exceptions: {}".format(
                                self.lastpos, index, self.match_count, self.exception_count))
                            sys.stdout.flush()
        except KeyboardInterrupt:
            print('Stopping at {} for {}@{}:{}'.format(self.lastpos, self.remote_user, self.hostname, self.path))
        sys.stdout.write("\n")
        sys.stdout.flush()
        return self.lastpos
