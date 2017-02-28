
import json
from django.db import models
from braces.views import LoginRequiredMixin
from datatableview import helpers
from datatableview import Datatable
from edc_bootstrap.views import EdcContextMixin
from edc_bootstrap.views import EdcDatatableView, EdcEditableDatatableView

from .models import Upload, History, Pending
from django.http.response import HttpResponse
from datatableview.columns import Column, DateColumn, DateTimeColumn, BooleanColumn, TextColumn
from getresults_dst.models import Acknowledgment, LogReaderHistory, RemoteFolder


class MyDatatable(Datatable):
    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"


class MyBooleanColumn(BooleanColumn):
    model_field_class = models.BooleanField
    handles_field_classes = [models.BooleanField, models.NullBooleanField]
    lookup_types = ('exact', 'in')

    def prep_search_value(self, term, lookup_type):
        return None


class UploadDatatable(Datatable):

    filename = TextColumn(
        "Filename",
        sources=['filename'])

    upload_user = TextColumn(
        "Upload user",
        sources=['upload_user'])

    upload_datetime = DateTimeColumn(
        "Upload Date",
        sources=['upload_datetime'],
        processor=helpers.format_date("%Y-%m-%d", localize=True))

    sent = MyBooleanColumn(
        "Sent",
        source=['sent'],
        processor=helpers.make_boolean_checkmark)

    sent_datetime = DateTimeColumn(
        "Sent Date",
        sources=['sent_datetime'],
        processor=helpers.format_date("%Y-%m-%d", localize=True))

    audited = MyBooleanColumn(
        'Audited',
        sources=['audited'],
        processor=helpers.make_boolean_checkmark)

    def make_boolean_yesno(self, instance, **kwargs):
        return 'Yes' if getattr(instance, kwargs.get('field_name')) is True else 'No'

    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"
        columns = [
            'id',
            'filename',
            'upload_datetime',
            'upload_user',
            'sent',
            'sent_datetime',
            'audited'
        ]


class UploadView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = Upload
    structure_template = "edc_bootstrap/bootstrap_structure.html"
    datatable_class = UploadDatatable
    ordering = ['-id']
    hidden_columns = ['id']
#     def get_table_data(self):
#         kwargs = {
#             'model': self.get_queryset().model,
#         }
#         if self.request.method in ('POST', 'PUT'):
#             kwargs.update({
#                 'data': self.request.POST,
#             })
#         return kwargs
# 
#     def update_qs(self, **kwargs):
#         return kwargs
# 
#     def post(self, request, *args, **kwargs):
#         table_data = self.get_table_data()
#         print('hello')
#         data = json.dumps({
#             'status': 'success',
#         })
#         return HttpResponse(data, content_type="application/json")


class SentHistoryDatatable(Datatable):

    filetimestamp = DateTimeColumn(
        'File Timestamp',
        sources=['filetimestamp'],
        processor=helpers.format_date("%Y-%m-%d", localize='True'))

    sent_datetime = DateTimeColumn(
        'Sent',
        sources=['sent_datetime'],
        processor=helpers.format_date("%Y-%m-%d", localize='True'))

    acknowledged = MyBooleanColumn(
        'Acknowledged',
        sources=['acknowledged'],
        processor=helpers.make_boolean_checkmark)

    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"
        columns = ['id', 'filename', 'archive', 'filetimestamp', 'sent_datetime',
                   'remote_hostname', 'remote_folder',
                   'acknowledged', 'ack_user', ]


class SentHistoryView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = History
    ordering = ['-sent_datetime']
    datatable_class = SentHistoryDatatable


class PendingDatatable(Datatable):
    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"


class PendingView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = Pending
    ordering = ['-id']
    datatable_class = PendingDatatable


class AcknowledgmentDatatable(Datatable):

    ack_datetime = DateTimeColumn(
        'Ack date',
        sources=['ack_datetime'],
        processor=helpers.format_date("%Y-%m-%d", localize='True'))

    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"


class AcknowledgmentView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = Acknowledgment
    ordering = ['-ack_datetime']
    hidden_columns = ['ack_string']
    datatable_class = AcknowledgmentDatatable


class LogReaderDatatable(Datatable):
    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"


class LogReaderView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = LogReaderHistory
    ordering = ['-id']
    hidden_columns = ['id']
    datatable_class = LogReaderDatatable


class RemoteFolderDatabale(Datatable):
    class Meta:
        structure_template = "edc_bootstrap/bootstrap_structure.html"


class RemoteFolderView(LoginRequiredMixin, EdcContextMixin, EdcDatatableView):
    model = RemoteFolder
    ordering = ['folder']
    hidden_columns = ['id']
    datatable_class = RemoteFolderDatabale
