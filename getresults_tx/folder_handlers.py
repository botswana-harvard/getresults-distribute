import os
import re

from getresults_tx.models import RemoteFolder


class FolderHandlerError(Exception):
    pass


class BaseFolderHandler(object):

    def select(self, instance, filename, mime_type, base_path):
        """ Selects the remote folder based on a 2 digit reference in the filename
        and the base path.

        Looks up folder_name from RemoteFolder.

        :param instance: instance of BaseDispatcher
        :param filename: filename without path.
        :param mime_type: mime_type as determined by magic.
        :param base_path: base path and in this case server.destination_dir
        :returns returns remote folder if found otherwise the base_path
        """
        remote_folder_path = None
        for label, folder_hint in self.folder_hints.items():
            try:
                obj = RemoteFolder.objects.get(
                    base_path=base_path.split('/')[-1:][0],
                    folder_hint=folder_hint(filename, mime_type),
                    label=label or None,
                )
                remote_folder_path = instance.remote_folder(
                    os.path.join(base_path, obj.folder),
                    mkdir_remote=instance.mkdir_remote)
                break
            except (RemoteFolder.DoesNotExist, FileNotFoundError):
                pass
        if not remote_folder_path:
            remote_folder_path = base_path
            label, folder_hint = None, None
        return remote_folder_path, (label, folder_hint)

    @property
    def folder_hints(self):
        """Returns a dictionary of {label: folder_hint_method} where label is the value of
        the attr on model RemoteFolder."""
        return {'': self.folder_hint}

    def folder_hint(self, filename, mime_type):
        return mime_type


class FolderHandler(BaseFolderHandler):
    """A folder handler that extracts a 2 digit folder_hint from
    filenames of three different formats.

    The folder_hint and label are used to query model RemoteFolder
    for the correct folder name.
    """
    def __init__(self):
        for label in self.folder_hints:
            if not RemoteFolder.objects.filter(label=label).exists():
                raise FolderHandlerError(
                    'Label \'{}\' does not exist in model RemoteFolder.'.format(label))

    @property
    def folder_hints(self):
        return {
            'bhs': self.bhs_folder_hint,
            'cdc1': self.cdc1_folder_hint,
            # 'cdc2': self.cdc2_folder_hint,
        }

    def bhs_folder_hint(self, filename, *args):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^066\-[0-9]{8}\-[0-9]{1}')
        return filename[4:6] if re.match(pattern, filename) else None

    def cdc1_folder_hint(self, filename, *args):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[123]{1}[0-9]{2}\-[0-9]{4}')
        return filename[1:3] if re.match(pattern, filename) else None

    def cdc2_folder_hint(self, filename, *args):
        """Returns a 2 digit code extracted from f if f matches the pattern,
        otherwise returns None."""
        pattern = re.compile(r'^[0-9]{2}\-[0-9]{3}\-[0-9]{2}\-[0-9]{2}')
        return filename[0:2] if re.match(pattern, filename) else None
