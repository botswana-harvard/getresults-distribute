import os
import re
import time

from django.utils import timezone
from paramiko import SFTPClient

from .event_handlers import BaseEventHandler


class LogLineHandler(object):

    def process(self, logline):
        print(logline)


class LogServer (BaseEventHandler):

    def __init__(self, logline_handler, hostname, logfile_path, timeout=None):
        super(LogServer, self).__init__(hostname, timeout)
        self.logline_handler = logline_handler()
        self.logfile_path = logfile_path
        self.last_position = 0
        self.ssh = self.connect()

    def watch(self, sleep, die=None):
        n = 0
        try:
            while n >= 0:
                self.read_log()
                time.sleep(sleep or 10)
                if die:
                    n += 1
                    if n == 2:
                        break
        except KeyboardInterrupt:
            self.stop()

    def read_log(self):
        if self.last_position == os.path.getsize(self.logfile_path):
            return None
        with SFTPClient.from_transport(self.ssh.get_transport()) as sftp:
            with sftp.open(self.logfile_path) as f:
                f.seek(self.last_position)
                loglines = f.readlines()
                self.last_position = f.tell()
                groups = (self.log_pattern.search(line.strip()) for line in loglines)
                for g in groups:
                    if g:
                        self.logline_handler.process(g.string)
        return None

    @property
    def log_pattern(self):
        return re.compile(r'{}'.format(timezone.now().strftime('^%b\ %d')))

    def stop(self):
        print('\n...stopping watch. Done')
