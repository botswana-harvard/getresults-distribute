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
import pwd

from django.conf import settings
from django.test.testcases import TestCase
from paramiko import AuthenticationException
from reportlab.pdfgen import canvas

from getresults_dst.event_handlers import RemoteFolderEventHandler
from getresults_dst.file_handlers import RegexPdfFileHandler
from getresults_dst.folder_handlers import BaseLookupFolderHandler
from getresults_dst.server import Server
from getresults_dst.utils import load_remote_folders_from_csv


class Tests(TestCase):

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

    def test_failed_authentication(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = '~/' + os.path.join(settings.BASE_DIR.split(os.path.expanduser('~/'))[1], 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        self.assertRaises(
            AuthenticationException,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
            remote_user='baddog'
        )

    def test_remote_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = '~/' + os.path.join(settings.BASE_DIR.split(os.path.expanduser('~/'))[1], 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
            remote_user=pwd.getpwuid(os.getuid()).pw_name
        )
        server = Server(event_handler)
        self.assertEquals(server.event_handler.destination_dir, os.path.join(settings.BASE_DIR, 'testdata/outbox'))

    def test_mime_type(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'])
        server = Server(event_handler)
        self.assertEquals(server.event_handler.mime_types, [b'text/plain'])

    def test_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        server = Server(event_handler)
        self.assertEquals(source_dir, server.event_handler.source_dir)
        self.assertEquals(destination_dir, server.event_handler.destination_dir)
        self.assertEquals(archive_dir, server.event_handler.archive_dir)

    def test_bad_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inboxnnnnn')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        self.assertRaises(
            FileNotFoundError,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outboxttt')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        self.assertRaises(
            FileNotFoundError,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archiiive')
        self.assertRaises(
            FileNotFoundError,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )

    def test_make_local_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = '/tmp/tmp_archive'
        try:
            os.rmdir('/tmp/tmp_archive')
        except IOError:
            pass
        self.assertRaises(
            FileNotFoundError,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        self.assertIsInstance(
            RemoteFolderEventHandler(
                source_dir=source_dir,
                destination_dir=destination_dir,
                archive_dir=archive_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt'],
                mkdir_local=True),
            RemoteFolderEventHandler,
        )
        os.rmdir('/tmp/tmp_archive')

    def test_make_remote_folder(self):
        try:
            os.rmdir('/tmp/tmp_getresults_dst_out')
        except IOError:
            pass
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join('/tmp/tmp_getresults_dst_out')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        self.assertRaises(
            FileNotFoundError,
            RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )

        self.assertIsInstance(
            RemoteFolderEventHandler(
                source_dir=source_dir,
                destination_dir=destination_dir,
                archive_dir=archive_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt'],
                mkdir_destination=True),
            RemoteFolderEventHandler,
        )
        self.assertIsInstance(
            RemoteFolderEventHandler(
                source_dir=source_dir,
                destination_dir=destination_dir,
                archive_dir=archive_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt']),
            RemoteFolderEventHandler,
        )
        try:
            os.rmdir('/tmp/tmp_getresults_dst_out')
        except IOError:
            pass

    def test_filter_listdir_filename_length(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
        )
        server = Server(event_handler)
        txt_50_filename = 'tmp1234567891234567891234567891234567891234567.txt'
        txt_51_filename = 'tmp12345678912345678912345678912345678912345678.txt'
        pdf_50_filename = 'tmp1234567891234567891234567891234567891234567.pdf'
        pdf_51_filename = 'tmp12345678912345678912345678912345678912345678.pdf'
        self.create_temp_pdf(os.path.join(source_dir, pdf_50_filename))
        self.create_temp_pdf(os.path.join(source_dir, pdf_51_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_50_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_51_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals([txt_50_filename], server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_50_filename, pdf_51_filename, txt_50_filename, txt_51_filename], server)

    def test_filter_listdir_txt(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
        )
        server = Server(event_handler)
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['tmp.txt'], server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_pdf(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
        )
        server = Server(event_handler)
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['tmp.pdf'], server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_pdf_wrong_mime(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['text/plain'],
        )
        server = Server(event_handler)
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals([], server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_unexpected_pattern_for_mime(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['text/plain'],
        )
        server = Server(event_handler)
        pdf_filename = 'tmp.pdf'
        txt_filename = 'i_am_a_text_file.pdf'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['i_am_a_text_file.pdf'], server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_converts_mime_type_to_byte(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '066-1200001-3.txt'
        with open(os.path.join(source_dir, filename), 'w') as f:
            f.write('hello earth')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'text/plain')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
            mkdir_destination=False)
        server = Server(event_handler)
        self.assertEqual(server.event_handler.mime_types, [b'text/plain'])
        for f in [filename]:
            for d in [server.event_handler.source_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_folder_handler_no_mkdir(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = RemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        folder_selection = BaseLookupFolderHandler().select(server, filename, b'application/pdf', server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, None)
        self.assertEquals(folder_selection.path, None)
        self.assertEquals(folder_selection.tag, None)
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass

