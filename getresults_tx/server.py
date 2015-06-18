# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import pwd
import time

from paramiko import SFTPClient
from paramiko import SSHClient
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException


class BaseDispatcher(object):

    def __init__(self, hostname=None, timeout=None):
        self.hostname = hostname or 'localhost'
        self.timeout = timeout or 5.0
        self.user = pwd.getpwuid(os.getuid()).pw_name

    def on_added(self, added):
        """Override for your needs.

        :param added: list of file names added to source_dir
        """
        pass

    def on_removed(self, removed):
        """Override for your needs.

        :param removed: list of file names removed from source_dir
                        and put in the destination_dir
        """
        pass

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


class Server(BaseDispatcher):

    def __init__(self, dispatcher, hostname=None, timeout=None,
                 source_dir=None, destination_dir=None, archive_dir=None,
                 file_prefix=None, file_suffix=None, exclude_existing_files=None,
                 mkdir_local=None, mkdir_remote=None):
        super(Server, self).__init__(hostname, timeout)
        self.dispatcher = dispatcher(hostname, timeout) or BaseDispatcher(hostname, timeout)
        self.hostname = hostname or 'localhost'
        self.port = 22
        self.timeout = timeout or 5.0
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
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
        """Moves files in source_dir to destination_dir.

        Returns the "after" list which is a list of filenames currently in source_dir.

        Calls on_added and on_removed handlers."""
        after = []
        for f in os.listdir(self.source_dir):
            if os.path.isfile(os.path.join(self.source_dir, f)):
                after.append(f)
        after = self.filter_by_filetype(after)
        added = [f for f in after if f not in before]
        removed = [f for f in before if f not in after]
        if added:
            self.dispatcher.on_added(added)
        if removed:
            self.dispatcher.on_removed(removed)
        return after

    def before(self):
        """Returns a list of files in the source_dir before the watch loop begins."""
        before = []
        if self.exclude_existing_files:
            for f in os.listdir(self.source_dir):
                if os.path.isfile(os.path.join(self.source_dir, f)):
                    before.append(f)
        before = self.filter_by_filetype(before)
        return before

    def local_folder(self, path):
        """Returns the path or raises an Exception if path does not exist."""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            if self.mkdir_local:
                os.makedirs(path)
            else:
                raise FileNotFoundError(path)
        return path

    def remote_folder(self, path):
        """Returns the path or raises an Exception if path does not exist on the remote host."""
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
        """Returns listdir as is or filtered by prefix and/or suffix."""
        if not self.file_prefix and not self.file_suffix:
            return listdir
        lst = []
        for f in listdir:
            if f.startswith(self.file_prefix or '') and f.endswith(self.file_suffix or ''):
                lst.append(f)
        return lst

    def mkdir_p(self, sftp, remote_directory):
        """Changes to this directory, recursively making new folders if needed.
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
