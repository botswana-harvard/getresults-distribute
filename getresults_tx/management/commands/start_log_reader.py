import re

from apache_log_parser import make_parser

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from getresults_tx.log_reader import LogReader
from getresults_tx.line_readers import RegexApacheLineReader


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):

        RegexApacheLineReader.line_parser = make_parser('%a %b %B %t %m %q %H %X %P %r %R')
        RegexApacheLineReader.pattern = re.compile(r'066\-[0-9]{8}\-[0-9]{1}[\_\-A-za-z0-9]{0,50}\.pdf')

        hostname = settings.GRTX_REMOTE_HOSTNAME
        user = settings.GRTX_REMOTE_USERNAME
        logfile = settings.GRTX_REMOTE_LOGFILE
        reader = LogReader(RegexApacheLineReader, hostname, user, logfile)
        try:
            reader.read()
        except Exception as e:
            raise CommandError(str(e))
