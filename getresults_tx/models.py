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
        max_length=25)

    path = models.CharField(
        max_length=200)

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
        max_length=50)

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
        verbose_name = 'Sent History'
        verbose_name_plural = 'Sent History'


class RemoteFolder(models.Model):

    folder = models.CharField(
        max_length=100)

    base_path = models.CharField(
        max_length=200)

    folder_hint = models.CharField(
        max_length=25,
        default=None,
        blank=True)

    label = models.CharField(
        max_length=10,
        null=True,
        blank=True)

    class Meta:
        app_label = 'getresults_tx'
        unique_together = (('folder', 'base_path'), ('folder', 'folder_hint'))
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
        if self.file:
            self.filename = self.file.name
            self.filesize = self.file.size
        super(Upload, self).save(*args, **kwargs)

    class Meta:
        app_label = 'getresults_tx'
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
        app_label = 'getresults_tx'
        ordering = ('filename', )
        verbose_name = 'Pending File'
        verbose_name_plural = 'Pending Files'

# @receiver(post_save, weak=False, dispatch_uid="enrollment_checklist_on_post_save")
# def update_mime_type_post_save(sender, instance, raw, created, using, **kwargs):
#     if not raw:
#         if isinstance(instance, Upload):
#             f = instance.file.open()
#             instance.mime_type = magic.from_file(f, mime=True)
#             f.close()