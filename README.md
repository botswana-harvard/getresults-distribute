[![Dependency Status](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e/badge.svg?style=flat)](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e)

# getresults-tx

Requires python3. Django 1.7 or 1.8.

For example:

    source_dir = os.path.join('~/getresult/upload')
    archive_dir = os.path.join('~/getresult/archive')
    destination_dir = os.path.join(~/getresults')
    
    server = Server(
		hostname='edc.example.com',
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types=['application/pdf'],
        file_patterns=['*.pdf'],
        touch_existing=True,
        )
    server.observe()

The server events are the `watchdog` events, namely; `on_created()`, `on_modifier()`, `on_moved()` and `on_deleted()`.


Setup
-----

Create your django project.

	django-admin startproject project

Install getresults-tx
	
	pip install -e git+https://github.com/botswana-harvard/getresults-tx@develop#g=getresults_tx

Add to `settings.py`:

	INSTALLED_APPS = (
	    ...
	    ...
	    'getresults_tx',
	    'project',
	)


	MEDIA_URL = '/media/'

	MEDIA_ROOT = os.path.expanduser('~/getresults_files/')

	# ssh-copy-id your key to the remote host first
	GRTX_REMOTE_HOSTNAME = 'edc.sample.com'
	GRTX_REMOTE_USERNAME = 'erikvw'

	# local folders are relative to MEDIA_ROOT
	GRTX_UPLOAD_FOLDER = 'upload/'
	GRTX_ARCHIVE_FOLDER = 'archive/'

	# remote folder, if relative, will be expanded 
	GRTX_REMOTE_FOLDER = '~/viral_load'

	# must specify both the pattern and mime type
	GRTX_FILE_PATTERNS = ['*.pdf']
	GRTX_MIME_TYPES = ['application/pdf']

Choose your database:

	DATABASES = {...}

Migrate:
	
	python manage.py makemigrations getresults_tx
	python manage.py migrate getresults_tx
	

Folders
-------

Create a local upload and archive folder. The server is set to `observe()` the `upload` folder. Once a file is
processed it is moved (`os.rename()`) to the archive folder.

The remote folder `destination_dir` will be created if it does not exist if `mkdir_remote=True`. If you specify 
`destination_dir='~/viral_load` and set `remote_hostname=edc.example.com` and `remote_user=erikvw`, then 
the remote folder will be, on linux, `/home/erikvw/viral_load` for user `erikvw@edc.example.com` or 
`/Users/erikvw/viral_load` on macosx. A custm folder handler can be passed to Server, `folder_handler`, to do more than
just copy the file to the remote folder. See `folder handlers` below. 


Event Handlers
--------------

The watchdog events are processed by an `event_handler`. Event handling can be customized by passing a custom
event handler. For example, the event handler `RemoteFolderEventHandler` sends files to a destination folder
on a remote host. 

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

Folder Handlers
---------------
A custom folder handler can be set on the event handler. For example, class `FolderHandler` collates files into 
sub folders in the remote folder. It determines the folder to target based on an expected pattern or _hint_ in
the filename. The hint is queried against model `RemoteFolder`, for example, match *12* from  *066-129999-9.pdf*

	RemoteFolder.objects.get(base_path=base_path, folder_hint='12', label='bhs') 
	
where `base_path` is `server.destination_dir`. See also `remote_folder.csv` in testdata.
     

File Handlers
-------------
A file handler is called when the observer selects files (`server.filter_listdir`). So in addition to checking
the `mime_type` and the `file_pattern` the file handler will be called. For example, class `FileHandler` 
attempts to extract text from a PDF and match a part of the filename to text in the PDF. In our case, the PDF
is a clinical test result. The PDF filenames are either a `specimen_identifier` or `subject_identifier`. Both
values must appear somewhere in the clinical test result. By checking the text we minimize the chance of
sending an incorrectly named PDF file.
    
SSH/SCP
-------

Files are always transferred using SCP. You need to setup key-based authentication first and check that it works between local and remote machines for the current account. This also applies if the _destination_ folder is on the same host as the _source_ folder.
