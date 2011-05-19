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

import unittest

from .. import gui


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


class TestGUI(unittest.TestCase):
    def setUp(self):
        '''Create the Application instance under test
        '''
        gui.init_i18n('en_US.UTF-8')
        self.rct = gui.Application('.')

    def test_window_exists(self):
        '''Check that the GTK+ window was created
        '''
        self.assertNotEqual(self.rct.window, None)


class TestSpanishTranslation(unittest.TestCase):
    def setUp(self):
        '''Create the Application instance under test
        '''
        gui.init_i18n('es_ES.UTF-8')
        self.rct = gui.Application('.')

    def test_window_title(self):
        self.assertEqual('Herramienta de configuracion de rsync', self.rct.window.get_title())

    # TODO: Add more tests


def get_suite():
    loader = unittest.TestLoader()
    return unittest.TestSuite([
        loader.loadTestsFromTestCase(TestLoadGUI),
        loader.loadTestsFromTestCase(TestGUI),
        loader.loadTestsFromTestCase(TestSpanishTranslation),
    ])
