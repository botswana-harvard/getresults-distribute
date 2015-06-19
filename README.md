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

An example that uses a custom *custom_select_destination_func* function on the handler:

    from getresults_tx.server import Server
    from getresults_tx.event_handlers import RemoteFolderEventHandler
    from getresults_tx.remote_folder_callbacks import select_sub_folder
    
    source_dir = '~/source/getresults-tx/getresults_tx/testdata/inbox/'
    destination_dir = '~/source/getresults-tx/getresults_tx/testdata/viral_load/'
    archive_dir = '~/source/getresults-tx/getresults_tx/testdata/archive/'
    
    RemoteFolderEventHandler.custom_select_destination_func=select_sub_folder
    
    server = Server(
        RemoteFolderEventHandler,
        hostname='localhost',
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types='application/pdf',
        mkdir_remote=True)
    server.watch()

For above, files are collated into sub-folders of the destination folder (*server.destination_dir*). The *custom_select_destination_func* parses the file name to lookup the destination sub-folder. The lookup is done against the _RemoteFolder_ model. For example, parse *12* from *066-129999-9.pdf*:
	
	RemoteFolder.objects.get(base_path=base_path, folder_hint='12') 
	
where *base_path* is *server.destination_dir*. See also *remote_folder.csv* in testdata.
    
    
    
