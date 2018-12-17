# Copyright (C) 2018 Fraunhofer FKIE
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import unittest

import conpot.core as conpot_core
from conpot.emulators.list import List


class TestBase(unittest.TestCase):

    def setUp(self):
        self._inner_keys = ['a', 'b']
        self._outer_key = 'dynamicMemoryBlockOfSize2'

        self.databus = conpot_core.get_databus()
        self.databus.set_value(self._outer_key, List(*self._inner_keys))

    def tearDown(self):
        self.databus.reset()

    def test_list_length_via_List(self):
        result = self.databus.get_value(self._outer_key)

        self.assertEqual(len(result), len(self._inner_keys))

    def test_read_unset_values_via_List(self):
        result = self.databus.get_value(self._outer_key)

        for i in range(len(result)):
            with self.assertRaises(AssertionError):
                _ = result[i]

    def test_read_set_values_via_List(self):
        expected = ['first', 'second']
        self.databus.set_value(self._inner_keys[0], expected[0])
        self.databus.set_value(self._inner_keys[1], expected[1])

        result = self.databus.get_value(self._outer_key)

        self.assertSequenceEqual(result, expected)

    def test_modify_values_via_List(self):
        expected = ['one', 'two']
        result = self.databus.get_value(self._outer_key)

        for idx in range(len(expected)):
            result[idx] = expected[idx]

        self.assertSequenceEqual(result, expected)

    def test_read_databus_via_List_exceeds_limit(self):
        result = self.databus.get_value(self._outer_key)
        out_of_bounds = len(result)

        with self.assertRaises(IndexError):
            _ = result[out_of_bounds]

    def test_write_databus_via_List_exceeds_limit(self):
        result = self.databus.get_value(self._outer_key)
        out_of_bounds = len(result)

        with self.assertRaises(IndexError):
            result[out_of_bounds] = 'bogus'
