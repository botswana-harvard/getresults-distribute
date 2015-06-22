import os

from django.conf import settings
from django.test.testcases import TestCase
from reportlab.pdfgen import canvas

from ..event_handlers import BaseEventHandler
from ..server import Server


class TestEventHandler(TestCase):

    def create_temp_txt(self, filename):
        with open(filename, 'w') as f:
            f.write('this is a test file')

    def create_temp_pdf(self, filename):
        c = canvas.Canvas(filename)
        c.drawString(100, 100, "Hello World")
        c.save()

    def remove_temp_files(self, files, server):
        for f in files:
            name = os.path.join(server.source_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass
        for f in files:
            name = os.path.join(server.destination_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass

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
            os.rmdir('/tmp/tmp_getresults_tx_out')
        except IOError:
            pass
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join('/tmp/tmp_getresults_tx_out')
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
            os.rmdir('/tmp/tmp_getresults_tx_out')
        except IOError:
            pass
