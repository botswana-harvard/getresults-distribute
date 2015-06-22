import os
import re

from getresults_tx.models import RemoteFolder


class FolderHandlerError(Exception):
    pass


class FolderSelection(object):

    def __init__(self, name, path, hint, label):
        self.name = name
        self.path = os.path.expanduser(path)
        self.hint = hint
        self.label = label

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.name, self.hint, self.label)

    def __str__(self):
        return self.name

PDF = b'application/pdf'


class BaseFolderHandler(object):

    def select(self, instance, filename, mime_type, base_path):
        """ Selects the remote folder uas returned by method :func:`folder_hint`.

        Folder name must be known to model RemoteFolder.

        :param instance: instance of BaseDispatcher
        :param filename: filename without path.
        :param mime_type: mime_type as determined by magic.
        :param base_path: base path and in this case server.destination_dir
        :returns returns a tuple of remote folder name (@type:str)and the folder_hint used
                 where folder_hint is a tuple of (label (@type: str), folder_hint (@type: str)).
        """
        remote_folder_path = None
        for label, folder_hint in self.folder_hints.items():
            try:
                folder_hint = folder_hint(filename, mime_type)
                obj = RemoteFolder.objects.get(
                    base_path=base_path.split('/')[-1:][0],
                    folder_hint=folder_hint,
                    label=label or None,
                )
                remote_folder_name = obj.folder
                remote_folder_path = instance.remote_folder(
                    os.path.join(base_path, remote_folder_name),
                    mkdir_remote=instance.mkdir_remote)
                break
            except (RemoteFolder.DoesNotExist, FileNotFoundError):
                pass
        if not remote_folder_path:
            remote_folder_name = None
            remote_folder_path = None
            label, folder_hint = None, None
        folder_selection = FolderSelection(remote_folder_name, remote_folder_path, folder_hint, label)
        return folder_selection

    @property
    def folder_hints(self):
        """Returns a dictionary of {label: folder_hint_method} where label is the value of
        the attr on model RemoteFolder."""
        return {'': self.folder_hint}

    def folder_hint(self, filename, mime_type):
        return mime_type


class FolderHandler(BaseFolderHandler):
    """A folder handler whose folder hints use regular expressions.

    The folder_hint and label are used to query model RemoteFolder
    for the correct folder name.
    """
    def __init__(self):
        for label in self.folder_hints:
            if not RemoteFolder.objects.filter(label=label).exists():
                raise FolderHandlerError(
                    'Remote folder label \'{}\' does not exist in model RemoteFolder.'.format(label))

    @property
    def folder_hints(self):
        return {
            'bhs': self.bhs_folder_hint,
            'cdc1': self.cdc1_folder_hint,
            # 'cdc2': self.cdc2_folder_hint,
        }

    def bhs_folder_hint(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^066\-[0-9]{8}\-[0-9]{1}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[4:6]
        return None

    def cdc1_folder_hint(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[123]{1}[0-9]{2}\-[0-9]{4}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[1:3]
        return None

    def cdc2_folder_hint(self, filename, mime_type):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[0-9]{2}\-[0-9]{3}\-[0-9]{2}\-[0-9]{2}')
        if mime_type == PDF and re.match(pattern, filename):
            return filename[0:2]
        return None
