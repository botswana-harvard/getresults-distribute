# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.contrib import admin

from .actions import (update_on_sent_action, upload_audit_action,
                      upload_unaudit_action, update_pending_files,
                      unacknowledge_action)
from .forms import UploadForm
from .models import History, RemoteFolder, Upload, Pending, Acknowledgment, LogReaderHistory


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):

    date_hierarchy = 'sent_datetime'

    list_display = ('filename', 'archive', 'filesize', 'filetimestamp',
                    'sent_datetime', 'ack_datetime', 'ack_user', 'mime_type',
                    'remote_hostname', 'remote_folder_tag',
                    'remote_folder')
    list_filter = ('sent_datetime', 'acknowledged', 'ack_datetime',
                   'remote_folder', 'remote_folder_tag', 'ack_user')
    search_fields = ('filename', 'ack_user')
    actions = [update_pending_files, unacknowledge_action]


@admin.register(RemoteFolder)
class RemoteFolderAdmin(admin.ModelAdmin):
    list_display = ('folder', 'label', 'folder_tag', 'base_path')
    list_filter = ('label', 'base_path')


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    form = UploadForm
    date_hierarchy = 'upload_datetime'
    fields = ('file', 'filename', 'upload_datetime', )
    readonly_fields = ('filename', 'upload_datetime', )
    list_display = ('filename', 'upload_datetime', 'upload_user', 'sent', 'sent_datetime',
                    'audited', 'filesize', 'mime_type')
    search_fields = ('file', 'description')
    list_filter = ('upload_datetime', 'sent', 'sent_datetime', 'audited_datetime', 'upload_user', 'auditor')
    search_fields = ('filename', )
    actions = [update_on_sent_action, upload_audit_action, upload_unaudit_action, update_pending_files]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('file', )
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.upload_user = request.user
        super(UploadAdmin, self).save_model(request, obj, form, change)


@admin.register(Pending)
class PendingAdmin(admin.ModelAdmin):
    date_hierarchy = 'filetimestamp'
    list_display = ('filename', 'filesize', 'filetimestamp', 'last_updated')
    list_filter = ('filetimestamp', )
    search_fields = ('filename', )
    actions = [update_pending_files, ]


@admin.register(Acknowledgment)
class AcknowledgmentAdmin(admin.ModelAdmin):
    date_hierachy = 'ack_datetime'
    list_display = ('filename', 'ack_user', 'ack_datetime', 'in_sent_history', 'created')
    list_filter = ('in_sent_history', 'ack_datetime', 'created', 'ack_user')
    search_fields = ('filename', 'ack_user')


@admin.register(LogReaderHistory)
class LogReaderHistoryAdmin(admin.ModelAdmin):
    date_hierachy = 'started'
    list_display = ('lastpos', 'lines', 'matches', 'exceptions', 'started', 'ended')
    list_filter = ('started', 'ended')
