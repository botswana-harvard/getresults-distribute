[![Build Status](https://travis-ci.org/botswana-harvard/getresults-distribute.svg)](https://travis-ci.org/botswana-harvard/getresults-distribute)
[![Code Health](https://landscape.io/github/botswana-harvard/getresults-distribute/develop/landscape.svg?style=flat)](https://landscape.io/github/botswana-harvard/getresults-distribute/develop)
[![Dependency Status](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e/badge.svg?style=flat)](https://www.versioneye.com/user/projects/558a5b6e306662001e00032e)
[![Coverage Status](https://coveralls.io/repos/botswana-harvard/getresults-distribute/badge.svg)](https://coveralls.io/r/botswana-harvard/getresults-distribute)

# getresults-distribute

Move files from a folder on server A to a folder on server B. If that's all you want, use `rsync`, otherwise read on.

We need accountability and management as well. This is our scenario:

* Our lab technicians upload result PDFs through the Django interface.
* `getresults_dst.server` moves and collates the uploaded clinical test results to a set of folders on remote server B. The PDF files are collated according to clinic facility (folder). A secure web resource serves up the PDF files on remote server B, e.g. ownCloud or apache, where each clinic is granted access to their PDF clinical results only.
* Our lab technicians check their work by confirming uploaded files were sent.
* The clinic staff access their files (download or view) from their facility. 
* `getresults_dst` contacts remote server B and scans the apache2 log for evidence that the files were accessed by the clinic.

We need to know that the clinic received the result. So in addition to just moving files, a detailed and searchable audit trail of what is happening is kept:
* searchable history of uploaded files
* searchable history of successfully sent files
* list of files uploaded but not sent (pending files)
* history of files accessed on server B (acknowledgments)
* full archive of all files sent
* searchable archive where each file is viewable through the django interface.

Requires python3. Django 1.7 or 1.8.

	>>> python manage.py start_observer
	
	Connected to host edc.sample.com.

	Server started on 2015-06-24 14:30:59.665896+00:00
	patterns: *.pdf
	mime: application/pdf
	Upload folder: /home/edc_user/getresults_files/upload
	Remote folder: remote_user@edc.sample.com:/home/remote_user/viral_load
	Archive folder: /home/edc_user/getresults_files/archive

	press CTRL-C to stop.


Look at the management command code but a very simple example is:

    source_dir = os.path.join('~/getresult/upload')
    archive_dir = os.path.join('~/getresult/archive')
    destination_dir = os.path.join(~/getresults')
    
    event_handler = SomeEventHandler(
		hostname='edc.example.com',
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types=['application/pdf'],
        file_patterns=['*.pdf'],
        touch_existing=True)
    
    server = Server(event_handler)
    server.observe()

The server events are the `watchdog` events, namely; `on_created()`, `on_modifier()`, `on_moved()` and `on_deleted()`.


Setup
-----

Create your django project.

	django-admin startproject project

Install getresults-distribute
	
	pip install -e git+https://github.com/botswana-harvard/getresults-distribute@develop#g=getresults_dst

Add to `settings.py`:

	INSTALLED_APPS = (
	    ...
	    ...
	    'getresults_dst',
	    'project',
	)


	FILE_UPLOAD_PERMISSIONS = 0o664

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
	GRTX_REMOTE_LOGFILE = '/var/log/apache2/access.log'

	# must specify both the pattern and mime type
	GRTX_FILE_PATTERNS = ['*.pdf']
	GRTX_MIME_TYPES = ['application/pdf']
	

Choose your database:

	DATABASES = {...}

Migrate:
	
	python manage.py makemigrations getresults_dst
	python manage.py migrate getresults_dst

Copy your ssh keys to the remote server:

    ssh-copy-id erikvw@edc.sample.com

Create your folders:

    $ mkdir ~/getresults_files/upload
    $ mkdir ~/getresults_files/archive
    $ ssh erikvw@edc.sample.com
    erikvw@edc.sample.com:~$ mkdir ~/viral_load

Get access rights to read the apache access.log or some part of it.
    
    '/var/log/apache2/access.log'

Load the list of remote folders

    python manage.py load_remote_folders

Start up django web server

    python manage.py runserver 0.0.0.0

Start the observer

    python manage.py start_observer

Start the log reader

    python manage.py start_log_reader


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
    
    from getresults_dst.server import Server
    from getresults_dst.event_handlers import RemoteFolderEventHandler
    from getresults_dst.folder_handlers import FolderHandler
    
    source_dir = '~/source/getresults-distribute/getresults_dst/testdata/inbox/'
    destination_dir = '~/source/getresults-distribute/getresults_dst/testdata/viral_load/'
    archive_dir = '~/source/getresults-distribute/getresults_dst/testdata/archive/'
    
    event_handler = RemoteFolderEventHandler(
		folder_handler=FolderHandler,    
        hostname='localhost',
        remote_user=remote_user,
        source_dir=source_dir,
        destination_dir=destination_dir,
        archive_dir=archive_dir,
        mime_types=['application/pdf'],
        file_patterns=['*.pdf'],
        touch_existing=True,
        mkdir_remote=True)
    server = Server(event_handler)
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
    
    
Log Reader
----------

The log reader uses `apache_log_parser` to parse a local or remote apache log. See the management command `start_log_reader`. We put this in a cron job. On the next parse event, the log reader starts where it left off (`lastpos`).

	#!/bin/bash
	. ~/.virtualenvs/django18/bin/activate
	cd ~/source/getresults-distribute
	python manage.py start_log_reader
	. ~/.virtualenvs/django18/bin/deactivate
	exit 0

Line Readers
------------
A line reader is passed to the log reader and called per line. For example, the `RegexApacheLineReader` reads a line looking for evidence that a previously sent file was accessed. If a match is found, the `Acknowledgement` model and the `History`
models are updated. 


SSH/SCP
-------

Files are always transferred using SCP. You need to setup key-based authentication first and check that it works between local and remote machines for the current account. This also applies if the _destination_ folder is on the same host as the _source_ folder.

Deployment on Apache
--------------------

As shown above, upload permissions used by Django are set to RW-RW-R-

	FILE_UPLOAD_PERMISSIONS = 0o664

Apache uses the www-data user. You cannot run the observer on this account. So you may choose to store files under
/var/www/data and add the observer account to www-data or store files in the home folder of the observer
and add www-data to the observer group. For example, if files are in the observer home folder:

	chgrp -R www-data ~/getresults_files/
	chgrp g+w www-data ~/getresults_files/

You should limit the request size that can be uploaded, `LimitRequestBody`, in the apache conf file, for example:

       Alias /media/ /home/observer/getresults_files/
        <Directory /home/observer/getresults_files >
          Require all granted
          LimitRequestBody 15000
        </Directory>
