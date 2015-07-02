# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Erik van Widenfelt
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import magic
import os

from django.conf import settings
from django.test.testcases import TestCase
from reportlab.pdfgen import canvas

from getresults_dst.getresults import GrRemoteFolderEventHandler
from getresults_dst.server import Server
from getresults_dst.utils import load_remote_folders_from_csv
from getresults_dst.file_handlers import BaseFileHandler
from paramiko.client import SSHClient
from getresults_dst.getresults.file_handlers import (
    GrBhsFileHandler, GrCdc1FileHandler, GrCdc2FileHandler, GrFileHandler)


class TestGetresults(TestCase):

    def create_temp_txt(self, filename, text=None):
        with open(filename, 'w') as f:
            f.write(text or 'this is a test file')

    def create_temp_pdf(self, filename, text=None):
        c = canvas.Canvas(filename)
        c.drawString(100, 200, 'hello world ' + str(text) + '\n' or "Hello World")
        c.showPage()
        c.save()

    def remove_temp_files(self, files, server):
        for f in files:
            for d in [server.event_handler.source_dir, server.event_handler.destination_dir]:
                name = os.path.join(d, f)
                try:
                    os.remove(name)
                except IOError:
                    pass

    def test_folder_handler_load_remotes_mkdir(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=BaseFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        server = Server(event_handler)
        with SSHClient() as event_handler.ssh:
            event_handler.connect()
            folder_selection = server.event_handler.folder_handler.select(
                server.event_handler, filename, b'application/pdf',
                server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.tag, '12')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(folder_selection.path)
        except IOError:
            pass

    def test_folder_handler_load_remotes_exists(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        remote_folder = os.path.join(destination_dir, 'digawana')
        try:
            os.makedirs(remote_folder)
        except FileExistsError:
            pass
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=BaseFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        with SSHClient() as event_handler.ssh:
            event_handler.connect()
            folder_selection = server.event_handler.folder_handler.select(
                server.event_handler, filename, b'application/pdf', server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'digawana')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'digawana'))
        self.assertEquals(folder_selection.tag, '12')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(remote_folder)
        except IOError:
            pass

    def test_file_handler_bhs(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '066-12000001-3')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrBhsFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        server.event_handler.file_handler.process(source_dir, filename, b'application/pdf')
        self.assertTrue(server.event_handler.file_handler.process(source_dir, filename, b'application/pdf'))
        self.assertEquals(server.event_handler.file_handler.match_string, '066-12000001-3')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), '12')
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_file_handler_cdc1(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '123-4567.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '123-4567')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc1FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        server.event_handler.file_handler.process(source_dir, filename, b'application/pdf')
        self.assertTrue(server.event_handler.file_handler.process(source_dir, filename, b'application/pdf'))
        self.assertEquals(server.event_handler.file_handler.match_string, '123-4567')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), '23')
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_file_handler_cdc2(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '12-345-67-89.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '12-345-67-89')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc2FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        server.event_handler.file_handler.process(source_dir, filename, b'application/pdf')
        self.assertTrue(server.event_handler.file_handler.process(source_dir, filename, b'application/pdf'))
        self.assertEquals(server.event_handler.file_handler.match_string, '12-345-67-89')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), '34')
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_folder_handler_bhs_selects_tag(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '066-12000001-3')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrBhsFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), '12')
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_folder_handler_cdc1_selects_tag(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '123-4567.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '123-4567')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc1FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        server.event_handler.file_handler.process(source_dir, filename, b'application/pdf')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), '23')
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_folder_handler_cdc2_selects_tag(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '12-345-67-89.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '12-345-67-89')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc2FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), '34')
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_folder_handler_all_selects_tag(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '066-12000001-3.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '12-345-67-89')
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=False)
        server = Server(event_handler)
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), '12')
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)
        filename = '123-4567.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '12-345-67-89')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), '23')
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), None)
        self.remove_temp_files([os.path.join(source_dir, filename)], server)
        filename = '12-345-67-89.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename), '12-345-67-89')
        self.assertEquals(server.event_handler.folder_handler.bhs_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc1_folder_tag_func(filename, b'application/pdf'), None)
        self.assertEquals(server.event_handler.folder_handler.cdc2_folder_tag_func(filename, b'application/pdf'), '34')
        self.remove_temp_files([os.path.join(source_dir, filename)], server)

    def test_filter_listdir_pdf_with_bhs_filehandler(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrBhsFileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
        )
        server = Server(event_handler)
        pdf_filenames = [
            'tmp.pdf', '066-12345678-9.pdf', '12-345-67-89.pdf', '123-4567.pdf', '1234567.pdf', '123456789.pdf']
        txt_filename = 'tmp.txt'
        for pdf_filename in pdf_filenames:
            self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertNotIn('tmp.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('1234567.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('123456789.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('12-345-67-89.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('123-4567.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertIn('066-12345678-9.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files(pdf_filenames + [txt_filename], server)

    def test_knows_folder_using_cdc1_file_handler(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '113-4567.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc1FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        server = Server(event_handler)
        with SSHClient() as event_handler.ssh:
            event_handler.connect()
            folder_selection = server.event_handler.folder_handler.select(
                server.event_handler, filename, b'application/pdf',
                server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'maunatlala')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'maunatlala'))
        self.assertEquals(folder_selection.tag, '13')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(folder_selection.path)
        except IOError:
            pass

    def test_knows_folder_using_cdc2_file_handler(self):
        load_remote_folders_from_csv()
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/viral_load')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        filename = '12-345-67-89.pdf'
        self.create_temp_pdf(os.path.join(source_dir, filename))
        self.assertEqual(magic.from_file(os.path.join(source_dir, filename), mime=True), b'application/pdf')
        event_handler = GrRemoteFolderEventHandler(
            file_handler=GrCdc2FileHandler,
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
            mkdir_destination=True)
        server = Server(event_handler)
        with SSHClient() as event_handler.ssh:
            event_handler.connect()
            folder_selection = server.event_handler.folder_handler.select(
                server.event_handler, filename, b'application/pdf',
                server.event_handler.destination_dir)
        self.assertEquals(folder_selection.name, 'gweta')
        self.assertEquals(folder_selection.path, os.path.join(server.event_handler.destination_dir, 'gweta'))
        self.assertEquals(folder_selection.tag, '34')
        try:
            os.remove(os.path.join(server.event_handler.source_dir, filename))
        except IOError:
            pass
        try:
            os.rmdir(folder_selection.path)
        except IOError:
            pass

    def test_filter_listdir_pdf_with_grfilehandler(self):
        source_dir = os.path.join(settings.BASE_DIR, 'testdata/inbox')
        destination_dir = os.path.join(settings.BASE_DIR, 'testdata/outbox')
        archive_dir = os.path.join(settings.BASE_DIR, 'testdata/archive')
        event_handler = GrRemoteFolderEventHandler(
            source_dir=source_dir,
            destination_dir=destination_dir,
            archive_dir=archive_dir,
            file_patterns=['*.pdf'],
            mime_types=['application/pdf'],
        )
        server = Server(event_handler)
        pdf_filenames = [
            'tmp.pdf', '066-12345678-9.pdf', '12-345-67-89.pdf', '123-4567.pdf', '1234567.pdf', '123456789.pdf']
        txt_filename = 'tmp.txt'
        for pdf_filename in pdf_filenames:
            self.create_temp_pdf(os.path.join(source_dir, pdf_filename))
        self.create_temp_txt(os.path.join(source_dir, txt_filename))
        listdir = os.listdir(source_dir)
        self.assertNotIn('tmp.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('1234567.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertNotIn('123456789.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertIn('066-12345678-9.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertIn('12-345-67-89.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.assertIn('123-4567.pdf', server.event_handler.filtered_listdir(listdir, source_dir))
        self.remove_temp_files(pdf_filenames + [txt_filename], server)
