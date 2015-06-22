# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.contrib import admin

from .models import History, RemoteFolder, Upload


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
    list_display = ('filename', 'upload_datetime', 'filesize', 'mime_type')
    search_fields = ('file', 'description')
admin.site.register(Upload, UploadAdmin)
