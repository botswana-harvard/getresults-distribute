# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

upload_fs = FileSystemStorage(location=settings.GRTX_UPLOAD_FOLDER)

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
        max_length=26)

    path = models.CharField(
        max_length=200)

    remote_path = models.CharField(
        max_length=200)

    remote_folder = models.CharField(
        max_length=27,
        default='default')

    remote_folder_tag = models.CharField(
        max_length=10,
        null=True,
        help_text='e.g. a value in the filename suggestive of the remote folder ...')

    archive_path = models.CharField(
        max_length=100,
        null=True)

    filename = models.CharField(
        max_length=50)

    filesize = models.FloatField()

    filetimestamp = models.DateTimeField()

    mime_type = models.CharField(
        max_length=28)

    status = models.CharField(
        max_length=15,
        choices=STATUS)

    sent_datetime = models.DateTimeField()

    acknowledged = models.BooleanField(
        default=False,
        blank=True,
    )

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
        app_label = 'getresults_dst'
        ordering = ('-sent_datetime', )
        verbose_name = 'Sent History'
        verbose_name_plural = 'Sent History'


class RemoteFolder(models.Model):

    folder = models.CharField(
        max_length=100)

    base_path = models.CharField(
        max_length=200)

    folder_tag = models.CharField(
        max_length=25,
        default=None,
        blank=True)

    label = models.CharField(
        max_length=10,
        default='default',
        help_text='key value in folder_tags dictionary.')

    class Meta:
        app_label = 'getresults_dst'
        unique_together = (('folder', 'base_path', 'label'), ('folder', 'folder_tag', 'label'))
        ordering = ('label', 'base_path', 'folder')
        verbose_name = 'Remote Folder Configuration'


class Upload(models.Model):

    file = models.FileField(
        upload_to=settings.GRTX_UPLOAD_FOLDER,
        null=True,
        blank=True)

    upload_datetime = models.DateTimeField(
        default=timezone.now
    )

    filename = models.CharField(
        max_length=50,
        null=True,
        blank=True)

    filesize = models.FloatField(
        null=True,
        blank=True)

    mime_type = models.CharField(
        max_length=25,
        null=True,
        blank=True)

    upload_user = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sent = models.BooleanField(
        default=False,
        blank=True,
        help_text='from history'
    )

    sent_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='from history'
    )

    audited = models.BooleanField(
        default=False,
        blank=True,
    )

    auditor = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    audited_datetime = models.DateTimeField(
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.id:
            if self.file:
                self.filename = os.path.split(self.file.name)[1]
                self.filesize = self.file.size
        super(Upload, self).save(*args, **kwargs)

    class Meta:
        app_label = 'getresults_dst'
        ordering = ('-upload_datetime', )


class Pending(models.Model):

    last_updated = models.DateTimeField(
        default=timezone.now
    )

    filename = models.CharField(
        max_length=50
    )

    filesize = models.FloatField()

    filetimestamp = models.DateTimeField()

    class Meta:
        app_label = 'getresults_dst'
        ordering = ('filename', )
        verbose_name = 'Pending File'
        verbose_name_plural = 'Pending Files'


class Acknowledgment(models.Model):

    filename = models.CharField(
        max_length=50
    )

    ack_user = models.CharField(
        max_length=50
    )

    ack_datetime = models.DateTimeField()

    ack_string = models.TextField(
        max_length=500
    )

    in_sent_history = models.BooleanField(
        default=False,
        help_text='True if ACK can be linked to sent history')

    created = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        app_label = 'getresults_dst'
        ordering = ('-ack_datetime', )


class AcknowledgmentUser(models.Model):

    ack_user = models.CharField(
        max_length=50,
        unique=True,
    )

    remote_folder = models.ForeignKey(RemoteFolder)

    created = models.DateTimeField(
        default=timezone.now
    )

    class Meta:
        app_label = 'getresults_dst'
        ordering = ('ack_user', )


class LogReaderHistory(models.Model):

    lastpos = models.IntegerField()

    lines = models.IntegerField(default=0)

    matches = models.IntegerField(default=0)

    exceptions = models.IntegerField(default=0)

    started = models.DateTimeField(
        default=timezone.now
    )

    ended = models.DateTimeField(null=True)

    class Meta:
        app_label = 'getresults_dst'
        ordering = ('-started', )
        verbose_name_plural = 'Log Reader History'
