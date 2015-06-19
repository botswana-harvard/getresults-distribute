# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

upload_fs = FileSystemStorage(location=settings.UPLOAD_FOLDER)

TX_SENT = 'sent'
TX_ACK = 'ack'

STATUS = (
    (TX_SENT, 'sent'),
    (TX_ACK, 'acknowledged'),
)


class History(models.Model):

    archive = models.FileField()

    hostname = models.CharField(
        max_length=25)

    remote_hostname = models.CharField(
        max_length=25)

    path = models.CharField(
        max_length=100)

    remote_path = models.CharField(
        max_length=200)

    remote_folder = models.CharField(
        max_length=25,
        default='default')

    remote_folder_hint = models.CharField(
        max_length=10,
        null=True,
        help_text='if filename is suggestive of the remote folder ...')

    archive_path = models.CharField(
        max_length=100,
        null=True)

    filename = models.CharField(
        max_length=25)

    filesize = models.FloatField()

    filetimestamp = models.DateTimeField()

    mime_type = models.CharField(
        max_length=25)

    status = models.CharField(
        max_length=15,
        choices=STATUS)

    sent_datetime = models.DateTimeField()

    ack_datetime = models.DateTimeField(
        null=True,
        blank=True)

    ack_user = models.CharField(
        max_length=50,
        null=True,
        blank=True)

    user = models.CharField(
        max_length=50)

    class Meta:
        app_label = 'getresults_tx'
        ordering = ('-sent_datetime', )


class RemoteFolder(models.Model):

    folder = models.CharField(
        max_length=100)

    base_path = models.CharField(
        max_length=100)

    folder_hint = models.CharField(
        max_length=10)

    class Meta:
        app_label = 'getresults_tx'
        unique_together = (('folder', 'base_path'), ('folder', 'folder_hint'))


class Upload(models.Model):

    file = models.FileField(upload_to='inbox/')

    upload_datetime = models.DateTimeField(
        default=timezone.now
    )

    filename = models.CharField(
        max_length=25,
        null=True,
        blank=True)

    filesize = models.FloatField(
        null=True,
        blank=True)

    def save(self, *args, **kwargs):
        self.filename = self.file.name
        self.filesize = self.file.size
        super(Upload, self).save(*args, **kwargs)

    class Meta:
        app_label = 'getresults_tx'
        ordering = ('-upload_datetime', )
