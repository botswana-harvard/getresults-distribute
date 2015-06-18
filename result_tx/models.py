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
        max_length=100)

    archive_path = models.CharField(
        max_length=100,
        null=True)

    filename = models.CharField(
        max_length=25)

    filesize = models.FloatField()

    filetimestamp = models.DateTimeField()

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
        app_label = 'result_tx'
        ordering = ('-sent_datetime', )


class RemoteFolder(models.Model):

    folder = models.CharField(
        max_length=100)

    base_path = models.CharField(
        max_length=100)

    folder_hint = models.CharField(
        max_length=10)

    class Meta:
        app_label = 'result_tx'
        unique_together = (('folder', 'base_path'), ('folder', 'folder_hint'))
