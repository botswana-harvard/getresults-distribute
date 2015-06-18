from django.contrib import admin

from .models import History


class HistoryAdmin(admin.ModelAdmin):

    date_hierarchy = 'sent_datetime'

    list_display = ('filename', 'filesize', 'filetimestamp', 'remote_hostname', 'status', 'sent_datetime', 'ack_datetime')
    list_filter = ('status', 'sent_datetime', 'ack_datetime')
    search_fields = ('filename', )
admin.site.register(History, HistoryAdmin)
