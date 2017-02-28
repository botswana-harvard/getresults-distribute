# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
from edc_bootstrap.views.edc_datatableview import EdcDatatableView
from getresults_dst.models import Pending, History

"""xx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from edc_bootstrap.views import LoginView, LogoutView, HomeView
from getresults_dst.views import (
    UploadView, SentHistoryView, PendingView, AcknowledgmentView, LogReaderView, RemoteFolderView)

admin.autodiscover()

urlpatterns = [
    url(r'^upload/$', UploadView.as_view(), name='upload_url'),
    url(r'^history/$', SentHistoryView.as_view(), name='sent_history_url'),
    url(r'^pending/$', PendingView.as_view(), name='pending_url'),
    url(r'^acknowledgment/$', AcknowledgmentView.as_view(), name='ack_url'),
    url(r'^log/$', LogReaderView.as_view(), name='log_url'),
    url(r'^remotefolder/$', RemoteFolderView.as_view(), name='remote_folder_url'),
    url(r'^login/', LoginView.as_view(), name='login_url'),
    url(r'^logout/', LogoutView.as_view(url='/'), name='logout_url'),
    url(r'^accounts/login/', LoginView.as_view()),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', HomeView.as_view(template_name="home.html"), name='home'),
]
