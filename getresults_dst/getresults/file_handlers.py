from getresults_dst.file_handlers import RegexPdfFileHandler


class GrBhsFileHandler(RegexPdfFileHandler):

    regex = r'066\-[0-9]{8}\-[0-9]{1}'
