from apache_log_parser import make_parser

from getresults_dst.getresults.patterns import BHS_PATTERN, CDC1_PATTERN, CDC2_PATTERN
from getresults_dst.log_line_readers import RegexApacheLineReader


class GrLogLineReader(RegexApacheLineReader):

    line_parser = make_parser('%a %b %B %t %m %q %H %X %P %r %R')
    regexes = [
        (BHS_PATTERN[1:] if BHS_PATTERN.startswith('^') else BHS_PATTERN) + '[\_\-A-za-z0-9]{0,50}\.pdf',
        (CDC1_PATTERN[1:] if CDC1_PATTERN.startswith('^') else CDC1_PATTERN) + '[\_\-A-za-z0-9]{0,50}\.pdf',
        (CDC2_PATTERN[1:] if CDC2_PATTERN.startswith('^') else CDC2_PATTERN) + '[\_\-A-za-z0-9]{0,50}\.pdf',
    ]
