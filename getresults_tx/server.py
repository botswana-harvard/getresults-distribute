import os
import pwd
import time

from paramiko import SFTPClient
from paramiko import SSHClient
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException


class Dispatcher(object):

    def __init__(self, hostname=None, timeout=None):
        self.hostname = hostname or 'localhost'
        self.timeout = timeout or 5.0
        self.user = pwd.getpwuid(os.getuid()).pw_name

    def on_added(self, added):
        print('Added: {}'.format(', '.join(added)))

    def on_removed(self, removed):
        print('Removed: {}'.format(', '.join(removed)))

    def connect(self):
        """Returns an ssh instance."""
        ssh = SSHClient()
        ssh.load_system_host_keys()
        try:
            ssh.connect(
                self.hostname,
                timeout=self.timeout
            )
        except AuthenticationException as e:
            raise AuthenticationException(
                'Got {}. Add user {} to authorized_keys on host {}'.format(
                    e, self.user, self.hostname))
        except BadHostKeyException as e:
            raise BadHostKeyException(
                'Add server to known_hosts on host {}.'
                ' Got {}.'.format(e, self.hostname))
        return ssh


class Server(Dispatcher):

    def __init__(self, dispatcher, hostname=None, timeout=None,
                 source_dir=None, destination_dir=None, archive_dir=None,
                 file_ext=None, exclude_existing_files=None, mkdir_local=None, mkdir_remote=None):
        super(Server, self).__init__(hostname, timeout)
        self.dispatcher = dispatcher(hostname, timeout) or Dispatcher(hostname, timeout)
        self.hostname = hostname or 'localhost'
        self.port = 22
        self.timeout = timeout or 5.0
        self.file_ext = file_ext or '.pdf'
        self.mkdir_remote = mkdir_remote
        self.mkdir_local = mkdir_local
        self.exclude_existing_files = exclude_existing_files
        self.source_dir = self.local_folder(source_dir)
        self.destination_dir = self.remote_folder(destination_dir)
        if archive_dir:
            self.archive_dir = self.local_folder(archive_dir)
        else:
            self.archive_dir = None
        dispatcher = self._wrapper(dispatcher)

    def _wrapper(self, dispatcher):
        dispatcher.source_dir = self.source_dir
        dispatcher.destination_dir = self.destination_dir
        dispatcher.archive_dir = self.archive_dir
        dispatcher.remote_folder = self.remote_folder
        return dispatcher

    def serve_forever(self):
        """Watches the source_dir for new files and copies them to the destination_dir."""
        before = self.before()
        while 1:
            time.sleep(5)
            before = self.watch(before)

    def watch(self, before):
        after = []
        for f in os.listdir(self.source_dir):
            if os.path.isfile(os.path.join(self.source_dir, f)):
                after.append(f)
        added = [f for f in after if f not in before]
        removed = [f for f in before if f not in after]
        if added:
            self.dispatcher.on_added(added)
        if removed:
            self.dispatcher.on_removed(removed)
        return after

    def before(self):
        """Returns a list of files in the source_dir BEFORE a watch loop session begins."""
        before = []
        if self.exclude_existing_files:
            for f in os.listdir(self.source_dir):
                if os.path.isfile(os.path.join(self.source_dir, f)):
                    before.append(f)
        return before

    def local_folder(self, path):
        """Returns the path or raises an Exception is it does not exist."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            if self.mkdir_local:
                os.makedirs(path)
            else:
                raise FileNotFoundError(path)
        return path

    def remote_folder(self, path):
        """Returns the path or raises an Exception is it does not exist."""
        path = os.path.expanduser(path)
        ssh = self.connect()
        with SFTPClient.from_transport(ssh.get_transport()) as sftp:
            try:
                sftp.chdir(path)
            except IOError:
                if self.mkdir_remote:
                    self.mkdir_p(sftp, path)
                else:
                    raise FileNotFoundError('{} not found on remote host.'.format(path))
        return path

    def filter_by_filetype(self, listdir):
        """Returns a filtered list if the file extension has been specified."""
        print(listdir)
        if not self.file_ext:
            return listdir
        return [f for f in listdir if f.endswith('.{}'.format(self.file_ext))]

    def mkdir_p(self, sftp, remote_directory):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if self.mkdir_remote:
            if remote_directory == '/':
                # absolute path so change directory to root
                sftp.chdir('/')
                return
            if remote_directory == '':
                # top-level relative directory must exist
                return
            try:
                sftp.chdir(remote_directory)  # sub-directory exists
            except IOError:
                dirname, basename = os.path.split(remote_directory.rstrip('/'))
                self.mkdir_p(sftp, dirname)  # make parent directories
                sftp.mkdir(basename)  # sub-directory missing, so created it
                sftp.chdir(basename)
                return True
