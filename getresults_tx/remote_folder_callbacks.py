import os
from getresults_tx.models import RemoteFolder


def select_sub_folder(filename, base_path, remote_folder_func, mkdir_remote):
    """Selects the remote folder based on a 2 digit reference in the filename
    and the base path.

    Looks up the folder name from RemoteFolder.

    :param filename: filename without path.

    :param base_path: base path and in this case server.destiniation_dir

    :param remote_folder_func: server.remote_folder or any function that can
                               confirm the remote folder exists and create
                               it if not.

    :param mkdir_remote: if True the remote folder func will create the remote folder
                         if it does not exist.

    :returns returns remote folder if found otherwise the base_path
    """
    folder_hint = filename[4:6]
    try:
        remote_folder = RemoteFolder.objects.get(
            base_path=base_path.split('/')[-1:][0],
            folder_hint=folder_hint
        )
        path = remote_folder_func(
            os.path.join(base_path, remote_folder.folder),
            mkdir_remote=mkdir_remote)
    except (RemoteFolder.DoesNotExist, FileNotFoundError) as e:
        print(str(e))
        path = base_path
    return path


def select_htc_folder(filename, *args):
    """11 characters 12-34-567-89
    YY-COMMUNITY-"""
    folder_hint = filename[3:5]


def select_ecc_folder(filename, *args):
    """8 characters XXX-XXXX"""
    folder_hint = filename[3:5]
