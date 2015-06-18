import csv
import os

from django.conf import settings

from ..models import RemoteFolder


def load_remote_folders_from_csv(csv_filename=None):
    csv_filename = csv_filename or os.path.join(settings.BASE_DIR, 'testdata/remote_folders.csv')
    with open(csv_filename, 'r') as f:
        reader = csv.reader(f, quotechar="'")
        header = next(reader)
        header = [h.lower() for h in header]
        for row in reader:
            r = dict(zip(header, row))
            try:
                RemoteFolder.objects.get(folder=r['folder'].strip().lower())
            except RemoteFolder.DoesNotExist:
                RemoteFolder.objects.create(
                    base_path=r['base_path'].strip().lower(),
                    folder=r['folder'].strip().lower(),
                    folder_hint=r['folder_hint'].strip().lower()
                )
