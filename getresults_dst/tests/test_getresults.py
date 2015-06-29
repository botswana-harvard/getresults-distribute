# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import magic
import os

from django.conf import settings
from django.test.testcases import TestCase
from reportlab.pdfgen import canvas

from getresults_dst.getresults import GrRemoteFolderEventHandler
from getresults_dst.server import Server
from getresults_dst.utils import load_remote_folders_from_csv


class TestGetresults(TestCase):

    def create_temp_txt(self, filename, text=None):
        with open(filename, 'w') as f:
            f.write(text or 'this is a test file')

    def create_temp_pdf(self, filename, text=None):
        c = canvas.Canvas(filename)
        c.drawString(100, 200, 'hello world ' + str(text) + '\n' or "Hello World")
        c.showPage()
        c.save()

    def remove_temp_files(self, files, server):
        for f in files:
            for d in [server.event_handler.source_dir, server.event_handler.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_folder_handler_load_remotes_mkdir(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=GrRemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        folder_selection = server.event_handler.folder_handler.select(
            server.event_handler, filename, b'application/pdf', server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.tag, '12')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(folder_selection.path)
        except IOError:
            pass

    def test_folder_handler_load_remotes_exists(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        remote_folder = os.path.join(destination_dir, 'digawana')
        try:
            os.makedirs(remote_folder)
        except FileExistsError:
            pass
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=GrRemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        folder_selection = server.event_handler.folder_handler.select(
            server.event_handler, filename, b'application/pdf', server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.tag, '12')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(remote_folder)
        except IOError:
            pass
