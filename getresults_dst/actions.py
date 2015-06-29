# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import pytz

from builtins import FileNotFoundError
from datetime import datetime

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.utils import timezone

from .models import History, Pending

tz = pytz.timezone(settings.TIME_ZONE)


def update_on_sent_action(modeladmin, request, uploads):
    for upload in uploads:
        try:
            history = History.objects.get(filename=upload.filename)
            upload.sent = True
            upload.sent_datetime = history.sent_datetime
        except MultipleObjectsReturned:
            history = History.objects.filter(filename=upload.filename).order_by('sent_datetime')
            upload.sent = True
            upload.sent_datetime = history[0].sent_datetime
        except History.DoesNotExist:
            upload.sent = False
            upload.sent_datetime = None
        try:
            upload.save()
        except FileNotFoundError:
            upload.file = None
            upload.save()
update_on_sent_action.short_description = "Check sent history"


def upload_audit_action(modeladmin, request, queryset):
    for obj in queryset:
        if obj.sent:
            obj.audited = True
            obj.audited_datetime = timezone.now()
            obj.auditer = request.user
            obj.save()
upload_audit_action.short_description = "Audit sent (flag uploads as audited if sent)"


def upload_unaudit_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.audited = False
        obj.audited_datetime = None
        obj.auditer = None
        obj.save()
upload_unaudit_action.short_description = "Undo audit (flag uploads as not audited)"


def update_pending_files(modeladmin, request, queryset):
    upload_path = os.path.join(settings.MEDIA_ROOT, settings.GRTX_UPLOAD_FOLDER)
    Pending.objects.all().delete()
    for filename in os.listdir(upload_path):
        fileinfo = os.stat(os.path.join(upload_path, filename))
        Pending.objects.create(
            filename=filename,
            filesize=fileinfo.st_size,
            filetimestamp=tz.localize(datetime.fromtimestamp(fileinfo.st_mtime))
        )
update_pending_files.short_description = "Update the list of uploaded files pending delivery."


def unacknowledge_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.ack_datetime = None
        obj.ack_user = None
        obj.acknowledged = False
        obj.save()
unacknowledge_action.short_description = "Undo an acknowledgement."
