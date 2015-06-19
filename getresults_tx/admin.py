# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.contrib import admin

from .models import History, RemoteFolder


class HistoryAdmin(admin.ModelAdmin):

    date_hierarchy = 'sent_datetime'

    list_display = ('filename', 'filesize', 'filetimestamp', 'mime_type',
                    'remote_hostname', 'status', 'remote_folder_hint',
                    'remote_folder',
                    'sent_datetime', 'ack_datetime')
    list_filter = ('status', 'sent_datetime', 'ack_datetime', 'remote_folder', 'remote_folder_hint')
    search_fields = ('filename', )
admin.site.register(History, HistoryAdmin)


class RemoteFolderAdmin(admin.ModelAdmin):
    list_display = ('folder', 'folder_hint', 'base_path')
admin.site.register(RemoteFolder, RemoteFolderAdmin)
