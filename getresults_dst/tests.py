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

from getresults_dst.event_handlers import BaseEventHandler
from getresults_dst.event_handlers import RemoteFolderEventHandler
from getresults_dst.file_handlers import RegexPdfFileHandler
from getresults_dst.folder_handlers import FolderHandler
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
            for d in [server.source_dir, server.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_failed_authentication(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = '~/' + os.path.join(settings.BASE_DIR.split(os.path.expanduser('~/'))[1], 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        self.assertRaises(
            AuthenticationException,
            Server,
            event_handler=BaseEventHandler,
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
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
            remote_user=pwd.getpwuid(os.getuid()).pw_name
        )
        self.assertEquals(server.destination_dir, os.path.join(settings.BASE_DIR, 'testdata/outbox'))

    def test_mime_type(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'])
        self.assertEquals(server.mime_types, [b'text/plain'])

    def test_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        self.assertEquals(source_dir, server.source_dir)
        self.assertEquals(destination_dir, server.destination_dir)
        self.assertFalse(server.archive_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        self.assertEquals(archive_dir, server.archive_dir)

    def test_bad_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inboxnnnnn')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        self.assertRaises(
            FileNotFoundError,
            Server,
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outboxttt')
        self.assertRaises(
            FileNotFoundError,
            Server,
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archiiive')
        self.assertRaises(
            FileNotFoundError,
            Server,
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )

    def test_make_local_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, '/tmp/tmp_archive')
        self.assertRaises(
            FileNotFoundError,
            Server,
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )
        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler,
                source_dir=source_dir,
                destination_dir=destination_dir,
                archive_dir=archive_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt'],
                mkdir_local=True),
            Server,
        )
        os.rmdir('/tmp/tmp_archive')

    def test_make_remote_folder(self):
        try:
            os.rmdir('/tmp/tmp_getresults_dst_out')
        except IOError:
            pass
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join('/tmp/tmp_getresults_dst_out')
        self.assertRaises(
            FileNotFoundError,
            Server,
            event_handler=BaseEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mime_types=['text/plain'],
            file_patterns=['*.txt'],
        )

        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler,
                source_dir=source_dir,
                destination_dir=destination_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt'],
                mkdir_remote=True),
            Server,
        )
        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler,
                source_dir=source_dir,
                destination_dir=destination_dir,
                mime_types=['text/plain'],
                file_patterns=['*.txt']),
            Server,
        )
        try:
            os.rmdir('/tmp/tmp_getresults_dst_out')
        except IOError:
            pass

    def test_filter_listdir_filename_length(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
        )
        txt_50_filename = 'tmp1234567891234567891234567891234567891234567.txt'
        txt_51_filename = 'tmp12345678912345678912345678912345678912345678.txt'
        pdf_50_filename = 'tmp1234567891234567891234567891234567891234567.pdf'
        pdf_51_filename = 'tmp12345678912345678912345678912345678912345678.pdf'
        self.create_temp_pdf(os.path.join(source_dir, pdf_50_filename))
        self.create_temp_pdf(os.path.join(source_dir, pdf_51_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_50_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_51_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals([txt_50_filename], server.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_50_filename, pdf_51_filename, txt_50_filename, txt_51_filename], server)

    def test_filter_listdir_txt(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
        )
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['tmp.txt'], server.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_pdf(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
        )
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['tmp.pdf'], server.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_pdf_wrong_mime(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['text/plain'],
        )
        pdf_filename = 'tmp.pdf'
        txt_filename = 'tmp.txt'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals([], server.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_filter_listdir_unexpected_pattern_for_mime(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['text/plain'],
        )
        pdf_filename = 'tmp.pdf'
        txt_filename = 'i_am_a_text_file.pdf'
        self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertEquals(['i_am_a_text_file.pdf'], server.filtered_listdir(listdir, source_dir))
        self.remove_temp_files([pdf_filename, txt_filename], server)

    def test_converts_mime_type_to_byte(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        filename = '066-1200001-3.txt'
        with open(os.path.join(source_dir, filename), 'w') as f:
            f.write('hello earth')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'text/plain')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.txt'],
            mime_types=['text/plain'],
            mkdir_remote=False)
        self.assertEqual(server.mime_types, [b'text/plain'])
        for f in [filename]:
            for d in [server.source_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_folder_handler_no_mkdir(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_remote=False)
        folder_selection = FolderHandler().select(server, filename, b'application/pdf', server.destination_dir)
        self.assertEquals(folder_selection.name, None)
        self.assertEquals(folder_selection.path, None)
        self.assertEquals(folder_selection.hint, None)
        self.assertEquals(folder_selection.label, None)
        try:
            os.remove(os.path.join(server.source_dir, filename))
        except IOError:
            pass

    def test_folder_handler_load_remotes_mkdir(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_remote=True)
        folder_selection = FolderHandler().select(server, filename, b'application/pdf', server.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.hint, '12')
        self.assertEquals(folder_selection.label, 'bhs')
        try:
            os.remove(os.path.join(server.source_dir, filename))
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
        remote_folder = os.path.join(destination_dir, 'digawana')
        os.makedirs(remote_folder)
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_remote=False)
        folder_selection = FolderHandler().select(server, filename, b'application/pdf', server.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.hint, '12')
        self.assertEquals(folder_selection.label, 'bhs')
        try:
            os.remove(os.path.join(server.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(folder_selection.path)
        except IOError:
            pass

    def test_file_handler(self):
        load_remote_folders_from_csv()
        RegexPdfFileHandler.regex = r'066\-[0-9]{8}\-[0-9]{1}'
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '066-12000001-3')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            file_handler=RegexPdfFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_remote=False)
        server.file_handler.process(source_dir, filename, b'application/pdf')
        self.assertTrue(server.file_handler.process(source_dir, filename, b'application/pdf'))
        self.assertEquals(server.file_handler.match_string, '066-12000001-3')
        self.remove_temp_files([os.path.join(source_dir, filename)], server)
