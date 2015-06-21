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
    server.watch()

The server events are on_added() and on_removed(). on_added() is called as new files are added to the source folder.
on_removed() is called as files are removed from the source folder. There may only one source folder per 
_Server_ instance.

The event handler `RemoteFolderEventHandler` sends files to a remote folder. With the custom folder 
handler `FolderHandler` files are collated into sub folders of the destination folder. Collation rules
are based on the filename. 

An example that uses a custom *FolderHandler* on the event handler:

    from getresults_tx.server import Server
    from getresults_tx.watchdog_event_handlers import RemoteFolderEventHandler
    from getresults_tx.folder_handlers import FolderHandler
    
    source_dir = '~/source/getresults-tx/getresults_tx/testdata/inbox/'
    destination_dir = '~/source/getresults-tx/getresults_tx/testdata/viral_load/'
    archive_dir = '~/source/getresults-tx/getresults_tx/testdata/archive/'
    
    RemoteFolderEventHandler.folder_handler=FolderHandler()
    
    server = Server(
        RemoteFolderEventHandler,
        hostname='localhost',
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types='application/pdf',
        file_patterns=['*.pdf'],
        mkdir_remote=True)
    server.observe()


For above, files are collated into sub-folders of the destination folder (*server.destination_dir*). The *custom_select_destination_func* parses the file name to lookup the destination sub-folder. The lookup is done against the _RemoteFolder_ model. For example, parse *12* from *066-129999-9.pdf*:
	
	RemoteFolder.objects.get(base_path=base_path, folder_hint='12') 
	
where *base_path* is *server.destination_dir*. See also *remote_folder.csv* in testdata.
    
SSH/SCP
-------

Files are always transferred using SCP. You need to setup key-based authentication first and check that it works between local and remote machines for the current account. This also applies if the _destination_ folder is on the same host as the _source_ folder.
