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
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/in')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/out')
        server = Server(dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        self.assertEquals(source_dir, server.source_dir)
        self.assertEquals(destination_dir, server.destination_dir)
        self.assertFalse(server.archive_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/in/archive')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir, archive_dir=archive_dir)
        self.assertEquals(archive_dir, server.archive_dir)

    def test_bad_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/innnnnn')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/out')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/in')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outttt')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir)
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/in/archive')
        self.assertRaises(
            FileNotFoundError,
            Server, dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            archive_dir=archive_dir)

    def test_make_local_folder(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/in')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/out')
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
            os.rmdir('/tmp/tmp_result_tx_out')
        except IOError:
            pass
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/in')
        destination_dir = os.path.join('/tmp/tmp_result_tx_out')
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
            os.rmdir('/tmp/tmp_result_tx_out')
        except IOError:
            pass

    def test_added_file(self):
        """Asserts an added file is moved to the destination."""
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/in')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/out')
        server = Server(
            dispatcher=Dispatcher, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True)
        before = server.before()
        name = os.path.join(server.source_dir, 'test.txt')
        open(name, 'w')
        before = server.watch(before)
        server.watch(before)
        name = os.path.join(server.destination_dir, 'test.txt')
        self.assertTrue(os.path.isfile(name))
