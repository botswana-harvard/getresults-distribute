import magic

import os

from reportlab.pdfgen import canvas
from django.test.testcases import TestCase
from django.conf import settings

from ..folder_handlers import FolderHandler
from ..event_handlers import RemoteFolderEventHandler
from ..server import Server
from ..utils import load_remote_folders_from_csv


class TestRemoteFolderEventHandler(TestCase):

    def create_temp_txt(self, filename):
        with open(filename, 'w') as f:
            f.write('this is a test file')

    def create_temp_pdf(self, filename):
        c = canvas.Canvas(filename)
        c.drawString(100, 100, "Hello World")
        c.save()

    def remove_temp_files(self, files, server):
        for f in files:
            for d in [server.source_dir, server.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

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
