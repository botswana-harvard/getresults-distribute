# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from getresults_dst.constants import PDF
from getresults_dst.folder_handlers import BaseLookupFolderHandler
from getresults_dst.event_handlers import RemoteFolderEventHandler

from .file_handlers import GrFileHandler
from .patterns import BHS_PATTERN, CDC1_PATTERN, CDC2_PATTERN

__all__ = ['GrRemoteFolderEventHandler']


class GrLookupFolderHandler(BaseLookupFolderHandler):
    """A folder handler whose folder tags use regular expressions.

    The folder_tag and label are used to query model RemoteFolder
    for the correct folder name.
    """
    @property
    def folder_tags(self):
        return {
            'bhs': self.bhs_folder_tag_func,
            'cdc1': self.cdc1_folder_tag_func,
            'cdc2': self.cdc2_folder_tag_func,
        }

    def bhs_folder_tag_func(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(BHS_PATTERN)
        if mime_type == PDF and re.match(pattern, filename):
            return filename[4:6]
        return None

    def cdc1_folder_tag_func(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(CDC1_PATTERN)
        if mime_type == PDF and re.match(pattern, filename):
            return filename[1:3]
        return None

    def cdc2_folder_tag_func(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(CDC2_PATTERN)
        if mime_type == PDF and re.match(pattern, filename):
            return filename[3:5]
        return None


class GrRemoteFolderEventHandler(RemoteFolderEventHandler):

    folder_handler = GrLookupFolderHandler()
    file_handler = GrFileHandler
    patterns = ['*.pdf']
