# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.contrib import admin

from .actions import update_on_sent_action, upload_audit_action, upload_unaudit_action, update_pending_files
from .models import History, RemoteFolder, Upload, Pending


class HistoryAdmin(admin.ModelAdmin):

    date_hierarchy = 'sent_datetime'

    list_display = ('filename', 'archive', 'filesize', 'filetimestamp',
                    'sent_datetime', 'ack_datetime', 'mime_type',
                    'remote_hostname', 'status', 'remote_folder_hint',
                    'remote_folder')
    list_filter = ('status', 'sent_datetime', 'ack_datetime', 'remote_folder', 'remote_folder_hint')
    search_fields = ('filename', )
admin.site.register(History, HistoryAdmin)


class RemoteFolderAdmin(admin.ModelAdmin):
    list_display = ('folder', 'label', 'folder_hint', 'base_path')
    list_filter = ('label', 'base_path')
admin.site.register(RemoteFolder, RemoteFolderAdmin)


class UploadAdmin(admin.ModelAdmin):
    date_hierarchy = 'upload_datetime'
    list_display = ('filename', 'upload_datetime', 'upload_user', 'sent', 'sent_datetime', 'audited', 'filesize', 'mime_type')
    search_fields = ('file', 'description')
    list_filter = ('upload_datetime', 'sent', 'sent_datetime', 'audited_datetime', 'upload_user', 'auditor')
    search_fields = ('filename', )
    actions = [update_on_sent_action, upload_audit_action, upload_unaudit_action, update_pending_files]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.upload_user = request.user
        super(UploadAdmin, self).save_model(request, obj, form, change)

admin.site.register(Upload, UploadAdmin)


class PendingAdmin(admin.ModelAdmin):
    date_hierarchy = 'filetimestamp'
    list_display = ('filename', 'filesize', 'filetimestamp', 'last_updated')
    list_filter = ('filetimestamp', )
    search_fields = ('filename', )
    actions = [update_pending_files, ]
admin.site.register(Pending, PendingAdmin)
