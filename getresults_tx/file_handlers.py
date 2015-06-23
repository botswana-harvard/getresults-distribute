import os
import re

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from .constants import PDF


class BaseFileHandler(object):

    def process(self, *args):
        return True


class RegexPdfFileHandler(BaseFileHandler):

    regex = None

    def __init__(self, regex=None):
        self.regex = regex or self.regex
        self.text = None
        self.match_string = None

    def process(self, path, filename, mime_type):
        pattern = re.compile(self.regex)
        match = re.match(pattern, filename)
        if mime_type == PDF and match:
            self.match_string = match.group()
            if self.match_string in self.pdf_to_text(filename, path):
                return True
        return False

    def pdf_to_text(self, filename, path):
        self.text = ''
        path = os.path.join(path, filename)
        with open(path, "rb") as f:
            try:
                pdf_file_reader = PdfFileReader(f)
                for page in pdf_file_reader.pages:
                    self.text = page.extractText()
            except TypeError:
                # pyDPF2 is not fully PY3 compatible
                # for some PDFs get a PY2/PY3 error
                # in <string>' requires string as left operand, not int
                # in the filter.py module
                # just forget it and return True
                return self.match_string
            except PdfReadError:
                pass
        return self.text
