[![Dependency Status](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e/badge.svg?style=flat)](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e)

# getresults-tx
transfer file based results, e.g. PDFs, to ?


For example:

    source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
    destination_dir = os.path.join(remote_base_dir, 'outbox')
    server = Server(
        event_handler=EventHandler,
        source_dir=source_dir,
        destination_dir=destination_dir,
        exclude_existing_files=True,
        mime_type='application/pdf',
        )
    server.observe()

The server events are the `watchdog` events, namely; `on_created()`, `on_modifier()`, `on_moved()` and `on_deleted()`.

Event handling can be customized by passing a custom event handler. For example, the event handler 
`RemoteFolderEventHandler` sends files to a destination folder on a remote host. By setting a custom
folder_handler on the event_handler, like `FolderHandler`, files are collated into sub folders of the destination folder
on the remote host. `FolderHandler` selects the sub-folder using folder "hints" defined on the folder_handler class. 

For example:

    import pwd
    
    from getresults_tx.server import Server
    from getresults_tx.event_handlers import RemoteFolderEventHandler
    from getresults_tx.folder_handlers import FolderHandler
    
    source_dir = '~/source/getresults-tx/getresults_tx/testdata/inbox/'
    destination_dir = '~/source/getresults-tx/getresults_tx/testdata/viral_load/'
    archive_dir = '~/source/getresults-tx/getresults_tx/testdata/archive/'
    
    RemoteFolderEventHandler.folder_handler=FolderHandler()
    remote_user = pwd.getpwuid(os.getuid()).pw_name
    
    server = Server(
        RemoteFolderEventHandler,
        hostname='localhost',
        remote_user=remote_user,
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types=['application/pdf'],
        file_patterns=['*.pdf'],
        touch_existing=True,
        mkdir_remote=True)
    server.observe()


On a server `observe` event, files are collated into sub-folders of the destination folder (`server.destination_dir`).
The sub-folder name is found by querying the `RemoteFolder` model using the folder_hint that matches the regular expression. For example, `re.match`es filename *066-129999-9.pdf* and then parses *12* as the folder hint.:
	
	RemoteFolder.objects.get(base_path=base_path, folder_hint='12', label='bhs') 
	
where `base_path` is `server.destination_dir`. See also `remote_folder.csv` in testdata.
    
SSH/SCP
-------

Files are always transferred using SCP. You need to setup key-based authentication first and check that it works between local and remote machines for the current account. This also applies if the _destination_ folder is on the same host as the _source_ folder.