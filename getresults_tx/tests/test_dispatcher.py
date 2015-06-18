from tempfile import mktemp
import os

from django.test.testcases import TestCase
from django.conf import settings

from ..dispatcher import Dispatcher
from ..server import Server


# class DummyServer(Server):
# 
#     def connect(self):
#         pass
# 
#     def remote_folder(self, path):
#         return Server.remote_folder(self, path)


class TestDispatcher(TestCase):

    def test_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        self.assertEquals(source_dir, server.source_dir)
        self.assertEquals(destination_dir, server.destination_dir)
        self.assertFalse(server.archive_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir)
        self.assertEquals(archive_dir, server.archive_dir)

    def test_bad_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inboxnnnnn')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outboxttt')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            archive_dir=archive_dir)

    def test_make_local_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, '/tmp/tmp_archive')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            archive_dir=archive_dir)
        self.assertIsInstance(
            Server(
                dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
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
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        self.assertIsInstance(
            Server(
                dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
                mkdir_remote=True),
            Server,
        )
        self.assertIsInstance(
            Server(
                dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir),
            Server,
        )
        try:
            os.rmdir('/tmp/tmp_getresults_tx_out')
        except IOError:
            pass

    def test_added_file(self):
        """Asserts an added file is moved to the destination."""
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True)
        before = server.before()
        name = os.path.join(server.source_dir, 'test.txt')
        open(name, 'w')
        before = server.watch_one(before)
        server.watch_one(before)
        name = os.path.join(server.destination_dir, 'test.txt')
        self.assertTrue(os.path.isfile(name))
        for f in ['test.txt']:
            for d in [server.source_dir, server.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_added_file_with_filter(self):
        """Asserts an added file is moved to the destination."""
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True, file_suffix='txt')
        before = server.before()
        name_watch = os.path.join(server.source_dir, 'test.txt')
        open(name_watch, 'w')
        name_ignore = os.path.join(server.source_dir, 'test.csv')
        open(name_ignore, 'w')
        before = server.watch_one(before)
        server.watch_one(before)
        name_watch = os.path.join(server.destination_dir, 'test.txt')
        self.assertTrue(os.path.isfile(name_watch))
        name_ignore = os.path.join(server.destination_dir, 'test.csv')
        self.assertFalse(os.path.isfile(name_ignore))
        for f in ['test.txt', 'test.csv']:
            for d in [server.source_dir, server.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_file_filter_no_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True)
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        for f in files:
            name = os.path.join(server.source_dir, f)
            open(name, 'w')
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        files.sort()
        self.assertEquals(files, listdir)
        for f in files:
            name = os.path.join(server.source_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass

    def test_file_filter_prefix_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_prefix='xxx')
        for f in files:
            name = os.path.join(server.source_dir, f)
            open(name, 'w')
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['xxxtest3.csv', 'xxxtest3.txt'], listdir)
        for f in files:
            name = os.path.join(server.source_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass

    def test_file_filter_suffix_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_suffix='csv')
        for f in files:
            name = os.path.join(server.source_dir, f)
            open(name, 'w')
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['test3.csv', 'xxxtest3.csv'], listdir)
        for f in files:
            name = os.path.join(server.source_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass

    def test_file_filter_both_filter(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        files = ['test1.txt', 'test2.txt', 'xxxtest3.txt', 'xxxtest3.csv', 'test3.csv']
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True,
            file_prefix='xxx', file_suffix='csv')
        for f in files:
            name = os.path.join(server.source_dir, f)
            open(name, 'w')
        listdir = server.before()
        listdir = server.filter_by_filetype(listdir)
        listdir.sort()
        self.assertEquals(['xxxtest3.csv'], listdir)
        for f in files:
            name = os.path.join(server.source_dir, f)
            try:
                os.remove(name)
            except IOError:
                pass
