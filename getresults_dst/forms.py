from django.core.exceptions import MultipleObjectsReturned
from django.forms import ModelForm, ValidationError

from .models import Upload, History


class UploadForm (ModelForm):

    def clean(self):
        cleaned_data = self.cleaned_data
        file = cleaned_data.get('file', None)
        try:
            filename = file.name
            self.raise_if_upload(filename)
            self.raise_if_history(filename)
        except AttributeError:
            pass
        return self.cleaned_data

    def raise_if_upload(self, filename):
        try:
            upload = Upload.objects.get(filename=filename)
            raise ValidationError(
                'File already uploaded. Got \'{}\' uploaded on \'{}\'.'.format(
                    filename, upload.upload_datetime.strftime('%Y-%m-%d %H:%M')))
        except MultipleObjectsReturned:
            upload_dates = []
            for upload in Upload.objects.filter(filename=filename).order_by('upload_datetime'):
                upload_dates.append(upload.upload_datetime.strftime('%Y-%m-%d %H:%M'))
            raise ValidationError(
                'File uploaded more than once already. Got  \'{}\' uploaded on {}.'.format(
                    filename, ', '.join(upload_dates)))
        except Upload.DoesNotExist:
            pass

    def raise_if_history(self, filename):
        try:
            history = History.objects.get(filename=filename)
            raise ValidationError(
                'File already uploaded and sent. Got \'{}\' sent on \'{}\'.'.format(
                    filename, history.sent_datetime.strftime('%Y-%m-%d %H:%M')))
        except MultipleObjectsReturned:
            sent_dates = []
            for history in History.objects.filter(filename=filename).order_by('sent_datetime'):
                sent_dates.append(history.sent_datetime.strftime('%Y-%m-%d %H:%M'))
            raise ValidationError(
                'File uploaded and sent more than once already. Got  \'{}\' sent on {}.'.format(
                    filename, ', '.join(sent_dates)))
        except History.DoesNotExist:
            pass

    class Meta:
        model = Upload
        fields = '__all__'
