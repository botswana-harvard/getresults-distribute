import sys

from django.core.management.base import BaseCommand, CommandError


from getresults_tx.utils import load_remote_folders_from_csv


class Command(BaseCommand):
    help = 'Load data from a folder containing remote_folders.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_filename', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            recs, added, updated = load_remote_folders_from_csv(options['csv_filename'][0])
            print('{} records (added {}, updated {}).'.format(recs, added, updated))
        except (FileNotFoundError, ) as e:
            sys.stdout.write('\n')
            raise CommandError(e)
