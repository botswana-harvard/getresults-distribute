import os

from django.test.testcases import TestCase
from django.conf import settings

from ..remote_folder_callbacks import select_folder
from ..event_handlers import RemoteFolderEventHandler
from ..models import RemoteFolder
from ..server import Server
from ..utils import load_remote_folders_from_csv


class TestRemoteFolderEventHandler(TestCase):

    def create_temp_file(self, name):
        with open(name, 'w') as f:
            f.write('this is a test file')

    def remove_temp_files(self, files, server):
        for f in files:
            for d in [server.source_dir, server.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_added_file(self):
        """Asserts an added file is moved to the destination."""
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            exclude_existing_files=True)
        before = server.before()
        name = os.path.join(server.source_dir, 'test.txt')
        self.create_temp_file(name)
        before = server.watch_once(before)
        before = server.watch_once(before)
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
            event_handler=RemoteFolderEventHandler, source_dir=source_dir, destination_dir=destination_dir,
            exclude_existing_files=True, file_suffix='txt')
        before = server.before()
        name_watch = os.path.join(server.source_dir, 'test.txt')
        self.create_temp_file(name_watch)
        name_ignore = os.path.join(server.source_dir, 'test.csv')
        self.create_temp_file(name_ignore)
        before = server.watch_once(before)
        server.watch_once(before)
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

    def test_select_destination_dir(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        server = Server(
            event_handler=RemoteFolderEventHandler, source_dir=source_dir, destination_dir=destination_dir)
        files = ['066-11.txt', '066-12.txt', '066-13.txt', '066-14.txt']
        for f in files:
            self.create_temp_file(os.path.join(server.source_dir, f))
        server.watch(die=True)
        files.sort()
        destination_files = os.listdir(server.destination_dir)
        destination_files.sort()
        self.assertEquals(files, destination_files)
        self.remove_temp_files(files, server)

    def test_select_destination_subdir(self):
        load_remote_folders_from_csv()
        self.assertEquals(RemoteFolder.objects.all().count(), 31)
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mkdir_remote=True)
        files = ['066-11.txt', '066-12.txt', '066-13.txt', '066-14.txt']
        for f in files:
            self.create_temp_file(os.path.join(server.source_dir, f))
        server.watch(die=True)
        files.sort()
        destination_files = os.listdir(server.destination_dir)
        destination_files.sort()
        self.assertEquals(files, destination_files)
        self.remove_temp_files(files, server)

    def test_select_folder_callback_no_remotes(self):
        filename = '066-12.txt'
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mkdir_remote=False)
        path = select_folder(filename, server.destination_dir, server.remote_folder, mkdir_remote=server.mkdir_remote)
        self.assertEquals(path, server.destination_dir)

    def test_select_folder_callback_load_remotes(self):
        load_remote_folders_from_csv()
        filename = '066-12.txt'
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mkdir_remote=False)
        path = select_folder(filename, server.destination_dir, server.remote_folder, mkdir_remote=server.mkdir_remote)
        self.assertEquals(path, server.destination_dir)

    def test_select_folder_callback_load_remotes_mkdir(self):
        load_remote_folders_from_csv()
        filename = '066-12.txt'
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mkdir_remote=True)
        path = select_folder(filename, server.destination_dir, server.remote_folder, mkdir_remote=server.mkdir_remote)
        self.assertNotEqual(path, server.destination_dir)
        self.assertEquals(path.split('/')[-1:], ['digawana'])
        try:
            os.rmdir(path)
        except IOError:
            pass

    def test_select_folder_callback_load_remotes_exists(self):
        load_remote_folders_from_csv()
        filename = '066-12.txt'
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        remote_folder = os.path.join(destination_dir, 'digawana')
        os.makedirs(remote_folder)
        server = Server(
            event_handler=RemoteFolderEventHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            mkdir_remote=True)
        path = select_folder(filename, server.destination_dir, server.remote_folder, mkdir_remote=server.mkdir_remote)
        self.assertNotEqual(path, server.destination_dir)
        self.assertEquals(path.split('/')[-1:], ['digawana'])
        try:
            os.rmdir(remote_folder)
        except IOError:
            pass
