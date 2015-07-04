from getresults_dst.file_handlers import RegexPdfFileHandler
from getresults_dst.getresults.patterns import BHS_PATTERN, CDC1_PATTERN, CDC2_PATTERN


class GrBhsFileHandler(RegexPdfFileHandler):

    regex = BHS_PATTERN


class GrCdc1FileHandler(RegexPdfFileHandler):

    regex = CDC1_PATTERN


class GrCdc2FileHandler(RegexPdfFileHandler):

    regex = CDC2_PATTERN


class GrFileHandler(RegexPdfFileHandler):

    regex = '|'.join([BHS_PATTERN, CDC1_PATTERN, CDC2_PATTERN])
