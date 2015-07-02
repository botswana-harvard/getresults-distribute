import socket
import time

from builtins import ConnectionRefusedError, ConnectionResetError
from django.utils import timezone
from paramiko import AutoAddPolicy
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException


class SSHConnectMixin(object):

    def connect(self, ssh=None):
        """Connects the ssh instance.

        If :param:`ssh` is not provided will connect `self.ssh`.
        """
        ssh = ssh if ssh else self.ssh
        ssh.load_system_host_keys()
        if self.trusted_host:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
        while True:
            try:
                ssh.connect(
                    self.hostname,
                    username=self.remote_user,
                    timeout=self.timeout,
                    compress=True,
                )
                print('Connected to host {}. '.format(self.hostname))
                break
            except (socket.timeout, ConnectionRefusedError) as e:
                print('{}. {} for {}@{}. Retrying ...'.format(
                    timezone.now(), str(e), self.remote_user, self.hostname)
                )
                time.sleep(5)
            except AuthenticationException as e:
                raise AuthenticationException(
                    'Got {} for user {}@{}'.format(
                        str(e)[0:-1], self.remote_user, self.hostname))
            except BadHostKeyException as e:
                raise BadHostKeyException(
                    'Add server to known_hosts on host {}.'
                    ' Got {}.'.format(e, self.hostname))
            except socket.gaierror:
                raise socket.gaierror('Hostname {} not known or not available'.format(self.hostname))
            except ConnectionResetError as e:
                raise ConnectionResetError('{} for {}@{}'.format(str(e), self.remote_user, self.hostname))
            except SSHException as e:
                raise SSHException('{} for {}@{}'.format(str(e), self.remote_user, self.hostname))

    def reconnect(self):
        self.connect()
