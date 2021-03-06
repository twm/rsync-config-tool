# coding: utf-8

# Copyright (C) 2011 Thomas W. Most
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''Tests for the rbconfig.gui module
'''

import os
import shutil
import tempfile
import unittest

import gtk
import mock

from .. import gui


def gtk_spin():
    '''Advance the GTK+ event loop until it runs out of events.
    '''
    while gtk.events_pending():
        gtk.main_iteration()

class TestLoadGUI(unittest.TestCase):
    def test_load(self):
        '''Simple sanity check on the loading process

        Run the load_gui function and check that the most important components
        have been loaded.
        '''
        builder = gui.load_gui()
        self.assertFalse(None is builder.get_object('main_window'))
        self.assertFalse(None is builder.get_object('rootselect_filechooserbutton'))
        self.assertFalse(None is builder.get_object('fstree_treeview'))
        self.assertFalse(None is builder.get_object('main_statusbar'))
        self.assertFalse(None is builder.get_object('aboutdialog'))


class BuilderAttrGetter(object):
    def __init__(self, builder):
        self.builder = builder

    def __getattr__(self, name):
        return self.builder.get_object(name)

class GUITestCase(unittest.TestCase):
    '''Base class for GUI test cases

    This class provides methods for constructing test directories and
    automatically constructs one defined by the test_dir_tree class variable,
    placing its location in the test_dir attribute.
    '''
    test_dir_tree = {} # Override in subclasses

    def setUp(self):
        '''Create the Application instance under test
        '''
        gui.init_i18n('en_US.UTF-8')
        self.test_dir = self.create_test_dir_tree(self.test_dir_tree)
        self.app = gui.Application()
        self.objects = BuilderAttrGetter(self.app.builder)

    def tearDown(self):
        '''Delete the test directory
        '''
        shutil.rmtree(self.test_dir)

    def create_test_dir_tree(self, tree_def):
        '''Create a directory tree for test purposes

        tree_def is a dictionary, its keys defining files and directories.
        Files are represented as integers indicating the size of the file to
        generate, and directories are dictionaries as tree_def.
        '''
        root = tempfile.mkdtemp()
        self._populate_test_dir(root, tree_def)
        return root

    def _populate_test_dir(self, parent, contents):
        '''Helper that populates the given parent directory
        '''
        # We deliberately don't do any error handling here, since the tests
        # would fail erroneously if we suppressed them.
        for name, value in contents.iteritems():
            path = os.path.join(parent, name)
            if isinstance(value, int): # Number of bytes to write to a file
                with open(path, 'wb+') as f:
                    while value > 0:
                        chunk_size = min(4096, value)
                        f.write('\0' * chunk_size)
                        value -= 4096
            elif isinstance(value, str): # String to write to a file
                with open(path, 'wb') as f:
                    f.write(value)
            else: # A directory
                os.mkdir(path)
                self._populate_test_dir(path, value)

    def get_filter_textview_contents(self):
        '''Get the textual contents of the filter_textview widget
        '''
        textbuffer = self.objects.filter_textview.get_buffer()
        return textbuffer.get_text(textbuffer.get_start_iter(),
                                   textbuffer.get_end_iter())

class TestBasicGUIOperations(GUITestCase):
    def test_window_exists(self):
        '''Check that the main window was created when the application started
        '''
        self.assertNotEqual(self.app.window, None)

    def test_window_destroy_callback(self):
        '''Check that the GTK+ mainloop ends when the window closes
        '''
        with mock.patch('gtk.main_quit') as main_quit:
            self.app.window.destroy()
            gtk_spin()
            main_quit.assert_called_with()


class TestFileMenus(GUITestCase):
    '''Test the items in the File menu

    See the docstrings for the activation handlers (in the Application class)
    for information on what they are supposed to do.
    '''
    test_dir_tree = {
        'filter_file': 'include foo\nexclude bar',
        'foo': { 'biz': 10 },
        'bar': { 'biz': 20 },
    }

    def test_file_new(self):
        self.objects.file_new_menu_item.activate()
        gtk_spin()
        self.assertEqual('', str(self.app.filters))
        self.assertEqual('', self.get_filter_textview_contents())

    def test_file_open(self):
        filter_fn = os.path.join(self.test_dir, 'filter_file')
        fcd = mock.Mock(spec=gtk.FileChooserDialog)
        fcd.get_filename.return_value = filter_fn
        fcd.run.return_value = gtk.RESPONSE_OK

        with mock.patch('gtk.FileChooserDialog') as FCD:
            FCD.return_value = fcd
            self.objects.file_open_menu_item.activate()
            FCD.assert_called_with(title=None,
                                   action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                   parent=self.app.window,
                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        fcd.destroy.assert_called_once_with()
        self.assertEqual('include foo\nexclude bar',
                         str(self.app.filters), 'Read file correctly')
        self.assertEqual('include foo\nexclude bar',
                         self.get_filter_textview_contents(), 'Contents displayed')

    def test_file_save_unsaved(self):
        filter_fn = os.path.join(self.test_dir, 'new_filter_file')
        chooser = mock.Mock(spec=gtk.FileChooserDialog)
        chooser.get_filename.return_value = filter_fn
        chooser.run.return_value = gtk.RESPONSE_OK

        with mock.patch('gtk.FileChooserDialog') as FCD:
            FCD.return_value = chooser

            self.assertTrue(self.app.filter_file is None, 'Not yet saved')
            self.objects.file_save_menu_item.activate()

            FCD.assert_called_with(title=None,
                                   action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                   parent=self.app.window,
                                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        chooser.destroy.assert_called_once_with() # Dialog is closed
        self.assertTrue(os.path.exists(filter_fn), 'File created')

    def test_file_save_again(self):
        filter_fn = os.path.join(self.test_dir, 'filter_file')

        self.app.filter_file = filter_fn
        self.objects.file_save_menu_item.activate()
        gtk_spin()

        # Check that the file was overwritten empty
        with open(filter_fn, 'rb') as f:
            self.assertEqual('', f.read(), 'File emptied')

        filter_fn2 = os.path.join(self.test_dir, 'filter_file2')
        self.app.filter_file = filter_fn2
        self.objects.file_save_menu_item.activate()
        gtk_spin()

        # Check that a new file was created, empty
        with open(filter_fn2, 'rb') as f:
            self.assertEqual('', f.read(), 'New file created empty')

    def test_file_save_as(self):
        filter_fn = os.path.join(self.test_dir, 'new_filter_fn')
        mock_dialog = mock.Mock(spec=gtk.FileChooserDialog)
        mock_dialog.get_filename.return_value = filter_fn
        mock_dialog.run.return_value = gtk.RESPONSE_OK

        with mock.patch('gtk.FileChooserDialog') as FCD:
            FCD.return_value = mock_dialog

            self.objects.file_save_as_menu_item.activate()
            gtk_spin()

            FCD.assert_called_once_with(title=None,
                                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                        parent=self.app.window,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            mock_dialog.destroy.assert_called_once_with()

        with open(filter_fn, 'rb') as f:
            self.assertEqual('', f.read(), 'Created file at correct location')

    def test_file_quit(self):
        '''Check that the GTK+ main loop is terminated when the application is quit
        '''
        with mock.patch('gtk.main_quit') as main_quit:
            self.objects.file_quit_menu_item.activate()
            gtk_spin()
            main_quit.assert_called_once_with()


class TestSpanishTranslation(unittest.TestCase):
    def setUp(self):
        '''Create the Application instance under test
        '''
        gui.init_i18n('es_ES.UTF-8')
        self.rct = gui.Application()
        self.builder = gui.load_gui()

    def test_window_title(self):
        self.assertEqual('Herramienta de configuracion de rsync', self.rct.window.get_title())

    def test_menubar(self):
        self.assertEqual(self.builder.get_object('menuitem1').get_child().get_text(), 'Archivo')
        self.assertEqual(self.builder.get_object('menuitem2').get_child().get_text(), 'Editar')
        self.assertEqual(self.builder.get_object('menuitem3').get_child().get_text(), 'Ver')
        self.assertEqual(self.builder.get_object('menuitem4').get_child().get_text(), 'Ayuda')

    def test_menu1_items(self):
        self.assertEqual(self.builder.get_object('file_new_menu_item').get_child().get_text(), 'Nuevo')
        self.assertEqual(self.builder.get_object('file_open_menu_item').get_child().get_text(), 'Abrir')
        self.assertEqual(self.builder.get_object('file_save_menu_item').get_child().get_text(), 'Guardar')
        self.assertEqual(self.builder.get_object('file_save_as_menu_item').get_child().get_text(), 'Guardar como')
        self.assertEqual(self.builder.get_object('file_quit_menu_item').get_child().get_text(), 'Salir')

    def test_menu2_items(self):
        self.assertEqual(self.builder.get_object('imagemenuitem6').get_child().get_text(), 'Cortar')
        self.assertEqual(self.builder.get_object('imagemenuitem7').get_child().get_text(), 'Copiar')
        self.assertEqual(self.builder.get_object('imagemenuitem8').get_child().get_text(), 'Pegar')
        self.assertEqual(self.builder.get_object('imagemenuitem9').get_child().get_text(), 'Eliminar')

    def test_menu3_items(self):
        self.assertEqual(self.builder.get_object('help_about_menu_item').get_child().get_text(), 'Acerca de')

def get_suite():
    loader = unittest.TestLoader()
    return unittest.TestSuite([
        loader.loadTestsFromTestCase(TestLoadGUI),
        loader.loadTestsFromTestCase(TestBasicGUIOperations),
        loader.loadTestsFromTestCase(TestFileMenus),
        loader.loadTestsFromTestCase(TestSpanishTranslation),
    ])
