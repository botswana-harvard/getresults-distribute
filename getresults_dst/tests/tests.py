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
import watchdog

from django.conf import settings
from django.core.files import File
from django.forms import ValidationError
from django.test.testcases import TestCase

from paramiko import AuthenticationException, SSHClient
from reportlab.pdfgen import canvas

from getresults_dst.event_handlers import RemoteFolderEventHandler, LocalFolderEventHandler
from getresults_dst.folder_handlers import BaseLookupFolderHandler, BaseFolderHandler
from getresults_dst.server import Server
from getresults_dst.utils import load_remote_folders_from_csv
from getresults_dst.log_line_readers import BaseLineReader
from getresults_dst.log_reader import LogReader
from getresults_dst.forms import UploadForm
from getresults_dst.models import Upload, History


class BaseTestCase(TestCase):

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

    def upload_remote_file_event(self, server, filename):
        with open(os.path.join(server.event_handler.source_dir, filename), 'rb') as f:
            upload = Upload()
            upload.file.name = File(f).name
            upload.save()
        event = watchdog.events.FileCreatedEvent(os.path.join(server.event_handler.source_dir, filename))
        with SSHClient() as server.event_handler.ssh:
            server.event_handler.connect()
            server.event_handler.on_created(event)

    def upload_file_event(self, server, filename):
        with open(os.path.join(server.event_handler.source_dir, filename), 'rb') as f:
            upload = Upload()
            upload.file.name = File(f).name
            upload.save()
        event = watchdog.events.FileCreatedEvent(os.path.join(server.event_handler.source_dir, filename))
        server.event_handler.on_created(event)


class Tests(BaseTestCase):

    def test_failed_authentication(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/uploadnnnnn')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archiiive')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/upload')
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
        folder_selection = BaseLookupFolderHandler().select(
            server, filename, b'application/pdf',
            server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, None)
        self.assertEquals(folder_selection.path, None)
        self.assertEquals(folder_selection.tag, None)
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass

    def test_log_base_line_reader(self):
        line_reader = BaseLineReader()
        ln = ('192.168.125.1 - - [03/Jul/2015:08:42:27 +0200] "GET /owncloud/index.php/apps/files/ajax'
              '/download.php?dir=%2FViral_Loads%2Fsefophe&files=066-22220024-0.pdf HTTP/1.1" 200 4294 "http'
              '://10.15.15.2/owncloud/apps/files_pdfviewer/vendor/pdfjs/build/pdf.worker.js?v=0.7" "Mozilla'
              '/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"')
        match_string = line_reader.on_newline(ln)
        self.assertEquals(match_string, '.pdf')

    def test_log_reader(self):
        txt = ('192.168.125.1 - - [03/Jul/2015:08:42:27 +0200] "GET /owncloud/index.php/apps/files/ajax'
               '/download.php?dir=%2FViral_Loads%2Fsefophe&files=066-22220024-0.pdf HTTP/1.1" 200 4294 "http'
               '://10.15.15.2/owncloud/apps/files_pdfviewer/vendor/pdfjs/build/pdf.worker.js?v=0.7" "Mozilla'
               '/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"')
        log_filename = os.path.join(settings.MEDIA_ROOT, 'test.log')
        self.create_temp_txt(log_filename, txt)
        log_reader = LogReader(BaseLineReader, None, None, log_filename)
        lastpos = log_reader.read()
        self.assertEquals(log_reader.last_read, '.pdf')
        self.assertEquals(lastpos, len(txt))
        try:
            os.remove(log_filename)
        except IOError:
            pass

    def test_line_reader_multiple_regex(self):
        txt = [
            ('192.168.125.1 - - [03/Jul/2015:08:42:27 +0200] "GET /owncloud/index.php/apps/files/ajax'
             '/download.php?dir=%2FViral_Loads%2Fsefophe&files=066-22220024-0.pdf HTTP/1.1" 200 4294 "http'
             '://10.15.15.2/owncloud/apps/files_pdfviewer/vendor/pdfjs/build/pdf.worker.js?v=0.7" "Mozilla'
             '/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"'),
            ('192.168.125.1 - - [03/Jul/2015:08:42:27 +0200] "GET /owncloud/index.php/apps/files/ajax'
             '/download.php?dir=%2FViral_Loads%2Fsefophe&files=erik.csv HTTP/1.1" 200 4294 "http'
             '://10.15.15.2/owncloud/apps/files_pdfviewer/vendor/pdfjs/build/pdf.worker.js?v=0.7" "Mozilla'
             '/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"'),
            ('192.168.125.1 - - [03/Jul/2015:08:42:27 +0200] "GET /owncloud/index.php/apps/files/ajax'
             '/download.php?dir=%2FViral_Loads%2Fsefophe&files=erik.txt HTTP/1.1" 200 4294 "http'
             '://10.15.15.2/owncloud/apps/files_pdfviewer/vendor/pdfjs/build/pdf.worker.js?v=0.7" "Mozilla'
             '/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"'),
        ]
        BaseLineReader.regexes = [r'\.txt', r'\.pdf', r'\.csv']
        line_reader = BaseLineReader()
        result = ['.pdf', '.csv', '.txt']
        for index, ln in enumerate(txt):
            match_string = line_reader.on_newline(ln)
            self.assertEquals(match_string, result[index])

    def test_upload_filename_no_change_on_resave(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_UPLOAD_FOLDER)
        destination_dir = os.path.expanduser(settings.GRTX_REMOTE_FOLDER)
        archive_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_ARCHIVE_FOLDER)
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '066-12000001-3')
        LocalFolderEventHandler.folder_handler = BaseFolderHandler()
        event_handler = LocalFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        server = Server(event_handler)

        self.upload_file_event(server, filename)
        upload = Upload.objects.get(filename=filename)
        upload.save()
        self.assertEquals(upload.filename, filename)
        self.remove_temp_files([filename], server)

    def test_upload_form_clean(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_UPLOAD_FOLDER)
        destination_dir = os.path.expanduser(settings.GRTX_REMOTE_FOLDER)
        archive_dir = os.path.join(settings.MEDIA_ROOT, settings.GRTX_ARCHIVE_FOLDER)
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '066-12000001-3')
        LocalFolderEventHandler.folder_handler = BaseFolderHandler()
        event_handler = LocalFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        server = Server(event_handler)

        self.upload_file_event(server, filename)
        self.assertIsInstance(Upload.objects.get(filename=filename), Upload)
        self.assertIsInstance(History.objects.get(filename=filename), History)
        self.assertRaises(ValidationError, UploadForm().raise_if_upload, filename)
        self.assertRaises(ValidationError, UploadForm().raise_if_history, filename)
        upload = Upload.objects.get(filename=filename)
        upload.save()
        self.assertEquals(upload.filename, filename)
        self.remove_temp_files([filename], server)
