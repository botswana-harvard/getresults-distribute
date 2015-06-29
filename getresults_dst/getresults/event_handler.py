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
        pattern = re.compile(r'^066\-[0-9]{8}\-[0-9]{1}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[4:6]
        return None

    def cdc1_folder_tag_func(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[123]{1}[0-9]{2}\-[0-9]{4}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[1:3]
        return None

    def cdc2_folder_tag_func(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[0-9]{2}\-[0-9]{3}\-[0-9]{2}\-[0-9]{2}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[3:5]
        return None


class GrRemoteFolderEventHandler(RemoteFolderEventHandler):

    folder_handler = GrLookupFolderHandler()
    patterns = ['*.pdf']
