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

import conpot.core as conpot_core
import logging
import ctypes

logger = logging.getLogger(__name__)


def _recalculate_szl_length(szl):
    list_of_szl_length_bytes = [len(szl) >> shift_amount & 0xFF for shift_amount in (8, 0)]
    szl[2] = list_of_szl_length_bytes[0]
    szl[3] = list_of_szl_length_bytes[1]


class SZLCreator(object):
    def __init__(self, szls):
        self.slz_persistence_list = []
        self.szls = szls
        self.data_bus = conpot_core.get_databus()

    def set_custom_identification_szls(self, server):
        """
        szl_0011 and szl_001c based on Snap7 example and pre-defined SZLs:
        https:#github.com/SCADACS/snap7/blob/a47805e169f02e8c68a57a7f9e7b4e73ff070b39/examples/plain-c/server.c
        https:#github.com/SCADACS/snap7/blob/a47805e169f02e8c68a57a7f9e7b4e73ff070b39/src/core/s7_firmware.h
        """

        # Create lists containing szl-data
        szl_0011 = self._create_szl_0011()
        szl_001c = self._create_szl_001C()

        # Set SZL length automatically
        _recalculate_szl_length(szl_0011)
        _recalculate_szl_length(szl_001c)

        # Set created szl-data in snap7
        self._set_szl_in_snap7(server, szl_0011, 0)
        self._set_szl_in_snap7(server, szl_001c, 1)

    def _create_szl_0011(self):
        szl_0011 = [
            0xFF,
            0x09,
            0x00, 0x60,  # Length of SZL
            0x00, 0x11,  # SZL ID
            0x00, 0x00, 0x00, 0x1C, 0x00, 0x04,

        ] + self.szls['0011']['module_identification']['id'] + \
            self.szls['0011']['module_identification']['text'] + [
            0x00, 0xC0,
        ] + self.szls['0011']['module_identification']['version'] + [  # Version X.Y
            0x00, 0x01,

        ] + self.szls['0011']['hardware_identification']['id'] + \
            self.szls['0011']['hardware_identification']['text'] + [
            0x00, 0xC0,
        ] + self.szls['0011']['hardware_identification']['version'] + [  # Version X.Y
            0x00, 0x01,

        ] + self.szls['0011']['firmware_identification']['id'] + \
            self.szls['0011']['firmware_identification']['text'] + [
            0x00, 0xC0,
            0x56,   # Belongs to version and is required for the v# to show-up, but any number seems to work
        ] + self.szls['0011']['firmware_identification']['version'] + [  # Version X.Y.Z for firmware
            # Boot Loader A
            0x00, 0x81, 0x42, 0x6F, 0x6F, 0x74, 0x20, 0x4C, 0x6F, 0x61,
            0x64, 0x65, 0x72, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
            0x20, 0x20, 0x00, 0x00, 0x41, 0x25, 0x0C, 0x0C
        ]

        return szl_0011

    def _create_szl_001C(self):
        szl_001c_data_list = []
        for szl_index in (self.szls['001C'].keys()):
            szl_001c_data_list.append(self.szls['001C'][szl_index]['id'] + self.szls['001C'][szl_index]['text'])

        szl_001c_data_list.sort(key=lambda i: (i[0] >> 8 & 0xFF) + i[1])  # Sort list by szl id
        szl_001c_data = []
        for data in szl_001c_data_list:
            szl_001c_data += data

        szl_001c = [
            0xFF,
            0x09,
            0x01, 0x5C,
            0x00, 0x1C,  # SZL ID
            0x00, 0x00, 0x00, 0x22, 0x00, 0x0A,
        ] + szl_001c_data

        return szl_001c

    def _set_szl_in_snap7(self, server, custom_szl_data, slz_identifier):
        data_to_share_with_snap7 = (ctypes.c_byte * len(custom_szl_data))()
        for idx in range(len(data_to_share_with_snap7)):
            data_to_share_with_snap7[idx] = custom_szl_data[idx]
        size = ctypes.sizeof(data_to_share_with_snap7)

        self.slz_persistence_list.append(data_to_share_with_snap7)  # Memory will be freed without this
        server.library.Srv_SetSZL(server.pointer, slz_identifier, data_to_share_with_snap7, size)
