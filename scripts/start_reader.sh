#!/bin/bash
. /home/bcpp/.virtualenvs/django18/bin/activate
cd /home/bcpp/source/getresults-distribute
python manage.py start_log_reader
exit 0
