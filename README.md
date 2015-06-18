# getresults-tx
transfer file based results, e.g. PDFs, to ?


For example:

    source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
    destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
    server = Server(
        dispatcher=Dispatcher,
        source_dir=source_dir,
        destination_dir=destination_dir,
        exclude_existing_files=True)
    server.watch()
