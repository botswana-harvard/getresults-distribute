# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os

from datetime import datetime

from .models import RemoteFolder
from getresults_dst.constants import PDF, TEXT


class FolderHandlerError(Exception):
    pass


class FolderSelection(object):
    """A class of the attributes of the folder to be returned to the event handler."""

    def __init__(self, folder_name, full_path, tag):
        self.name = folder_name
        try:
            self.path = os.path.expanduser(full_path)
        except AttributeError:
            self.path = None
        self.tag = tag

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.name, self.tag)

    def __str__(self):
        return self.name


class BaseFolderHandler(object):

    folder_selection = FolderSelection

    def select(self, instance, filename, mime_type, base_path):
        """Called by the event handler."""
        folder_name, full_path, tag = self.select_folder(instance, filename, mime_type, base_path)
        return self.folder_selection(folder_name, full_path, tag)

    def select_folder(self, instance, filename, mime_type, base_path):
        """Override to select a folder"""
        folder_name, full_path, tag = 'folder', os.path.join(base_path, 'folder'), None
        return folder_name, full_path, tag


class MimeTypeFolderHandler(BaseFolderHandler):

    def select_folder(self, instance, filename, mime_type, base_path):
        """Select a folder based on the mime_type"""
        if mime_type == PDF:
            folder_name, tag = PDF, PDF
        elif mime_type == TEXT:
            folder_name, tag = TEXT, TEXT
        else:
            folder_name, tag = 'unknown', 'unknown'
        full_path = os.path.join(base_path, folder_name)
        return folder_name, full_path, tag


class DayFolderHandler(BaseFolderHandler):

    def select_folder(self, instance, filename, mime_type, base_path):
        """Select a folder based on today's date."""
        folder_name = datetime.today().strftime('%Y%m%d')
        full_path = os.path.join(base_path, folder_name)
        tag = datetime.today().strftime('%w')
        return folder_name, full_path, tag


class BaseLookupFolderHandler(BaseFolderHandler):

    def select_folder(self, event_handler, filename, mime_type, base_path):
        """ Looks up the remote folder in model RemoteFolder using the tag, returned by
        :func:`folder_tag_func`, base_path and label.

        Folder name must be known to model RemoteFolder.

        :param event_handler: instance of BaseEventHandler
        :param filename: filename without path.
        :param mime_type: mime_type as determined by magic.
        :param base_path: base path, e.g server.destination_dir
        """
        full_path = None
        for label, folder_tag_func in self.folder_tags.items():
            try:
                try:
                    tag = folder_tag_func(filename, mime_type)
                except TypeError as e:
                    if 'object is not callable' in str(e):
                        tag = folder_tag_func
                    else:
                        raise
                folder_name = RemoteFolder.objects.get(
                    base_path=base_path.split('/')[-1:][0],
                    folder_tag=tag,
                    label=label).folder
                full_path = event_handler.check_destination_path(
                    os.path.join(base_path, folder_name),
                    mkdir_destination=event_handler.mkdir_destination)
                break
            except (RemoteFolder.DoesNotExist, FileNotFoundError):
                pass
        if not full_path:
            folder_name = None
            full_path = None
            tag = None
        return folder_name, full_path, tag

    @property
    def folder_tags(self):
        """Override to return a dictionary of {label: folder_tag_func} where label is the value of
        the attr on model RemoteFolder.

        There should be one item per folder tag in RemoteFolder.

        See getresults.folder_handlers for an example."""
        return {'default': self.folder_tag_func}

    def folder_tag_func(self, filename, mime_type):
        """Override to return a folder tag that will be used to query against RemoteFolder.

        You will define as many of these methods as are added to the folder_tags dictionary.
        """
        folder_tag = 'default'
        return folder_tag
