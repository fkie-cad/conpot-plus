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

from collections import MutableSequence

import conpot.core as conpot_core


class List(MutableSequence):
    """Treat a bunch of databus keys as a list-like object"""
    def __init__(self, *args):
        self._databus = conpot_core.get_databus()
        self._keys = args

    # Called by databus. Return ourselves and pretend to be a list-like object.
    def get_value(self):
        return self

    def insert(self, index, object):
        raise NotImplementedError

    def __len__(self):
        return len(self._keys)

    def __delitem__(self, v):
        raise NotImplementedError

    def __getitem__(self, idx):
        return self._databus.get_value(self._keys[idx])

    def __setitem__(self, idx, value):
        return self._databus.set_value(self._keys[idx], value)
