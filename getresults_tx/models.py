# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from django.db import models

TX_SENT = 'sent'
TX_ACK = 'ack'

STATUS = (
    (TX_SENT, 'sent'),
    (TX_ACK, 'acknowledged'),
)


class History(models.Model):

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

    subject_identifier = models.CharField(
        max_length=25)

    status = models.CharField(
        max_length=15,
        choices=STATUS)

    sent_datetime = models.DateTimeField()

    ack_datetime = models.DateTimeField(
        null=True)

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
