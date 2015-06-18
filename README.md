# getresults-tx
transfer file based results, e.g. PDFs, to ?


For example:

    source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
    destination_dir = os.path.join(remote_base_dir, 'outbox')
    server = Server(
        dispatcher=Dispatcher,
        hostname='example.com',
        source_dir=source_dir,
        destination_dir=destination_dir,
        exclude_existing_files=True,
        file_suffix='.pdf')
    server.watch()
