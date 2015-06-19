import os

from django.test.testcases import TestCase
from django.conf import settings

from ..event_handlers import BaseEventHandler
from ..server import Server


class TestEventHandler(TestCase):

    def create_temp_file(self, name):
        with open(name, 'w') as f:
            f.write('this is a test file')

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
        server = Server(event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        self.assertEquals(source_dir, server.source_dir)
        self.assertEquals(destination_dir, server.destination_dir)
        self.assertFalse(server.archive_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir)
        self.assertEquals(server.mime_types, [b'text/plain'])

    def test_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        self.assertEquals(source_dir, server.source_dir)
        self.assertEquals(destination_dir, server.destination_dir)
        self.assertFalse(server.archive_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir)
        self.assertEquals(archive_dir, server.archive_dir)

    def test_bad_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inboxnnnnn')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        self.assertRaises(
            FileNotFoundError,
            Server, event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outboxttt')
        self.assertRaises(
            FileNotFoundError,
            Server, event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        self.assertRaises(
            FileNotFoundError,
            Server, event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            archive_dir=archive_dir)

    def test_make_local_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, '/tmp/tmp_archive')
        self.assertRaises(
            FileNotFoundError,
            Server, event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            archive_dir=archive_dir)
        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
                archive_dir=archive_dir, mkdir_local=True),
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
            Server, event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
                mkdir_remote=True),
            Server,
        )
        self.assertIsInstance(
            Server(
                event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir),
            Server,
        )
        try:
            os.rmdir('/tmp/tmp_getresults_tx_out')
        except IOError:
            pass

    def test_file_filter_no_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True)
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        for f in files:
            name = os.path.join(server.source_dir, f)
            self.create_temp_file(name)
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        files.sort()
        self.assertEquals(files, listdir)
        self.remove_temp_files(files, server)

    def test_file_filter_prefix_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_prefix='xxx')
        for f in files:
            name = os.path.join(server.source_dir, f)
            self.create_temp_file(name)
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['xxxtest3.csv', 'xxxtest3.txt'], listdir)
        self.remove_temp_files(files, server)

    def test_file_filter_suffix_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_suffix='csv')
        for f in files:
            name = os.path.join(server.source_dir, f)
            self.create_temp_file(name)
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['test3.csv', 'xxxtest3.csv'], listdir)
        self.remove_temp_files(files, server)

    def test_file_filter_both_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            event_handler=BaseEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_prefix='xxx', file_suffix='csv')
        for f in files:
            name = os.path.join(server.source_dir, f)
            self.create_temp_file(name)
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['xxxtest3.csv'], listdir)
        self.remove_temp_files(files, server)
