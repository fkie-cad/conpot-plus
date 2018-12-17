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

import gevent.monkey
gevent.monkey.patch_all()

import logging
import unittest
from collections import namedtuple
import gevent
import conpot.core as conpot_core
from conpot.protocols.snap7.snap7_server import Snap7Server

from snap7.client import Client
from snap7.server import logger
from snap7.snap7exceptions import Snap7Exception


class TestBase(unittest.TestCase):
    def setUp(self):
        self.databus = conpot_core.get_databus()
        self.databus.initialize('conpot/templates/snap7_server/template.xml')
        args = namedtuple('FakeArgs', '')
        logger.setLevel(logging.WARNING)
        self.snap7_instance = Snap7Server('conpot/templates/snap7_server/snap7/snap7.xml', 'none', args)
        gevent.spawn(self.snap7_instance.start, '127.0.0.1', 60102)
        gevent.sleep(0.5)
        self.server_port = 60102

        self.client = Client()
        self.client.create()
        self.client.connect("127.0.0.1", 0, 0, tcpport=self.server_port)

    def tearDown(self):
        self.client.disconnect()
        gevent.sleep(1)
        self.snap7_instance.stop()

    def test_info(self):
        expected = {
            'ModuleTypeName': 'Some CPU',
            'SerialNumber': '123456789',
            'ASName': 'Some system',
            'Copyright': 'Someone',
            'ModuleName': 'Some PLC'
        }

        info = self.client.get_cpu_info()
        param_list = [param[0] for param in info._fields_]
        result = {}
        for param in param_list:
            result[param] = getattr(info, param)

        self.assertSequenceEqual(expected.keys(), result.keys())
        for key, val in result.items():
            self.assertEquals(expected[key], val)

    def test_cpu_state(self):
        expected = "S7CpuStatusRun"
        state = self.client.get_cpu_state()
        self.assertEquals(state, expected)

    def test_cpu_stop(self):
        expected = "S7CpuStatusStop"
        self.client.plc_stop()
        state = self.client.get_cpu_state()
        self.assertEquals(state, expected)

    def test_cpu_start(self):
        expected = "S7CpuStatusRun"
        self.client.plc_stop()
        self.client.plc_cold_start()
        state = self.client.get_cpu_state()
        self.assertEquals(state, expected)

        self.client.plc_stop()
        self.client.plc_hot_start()
        self.assertEquals(state, expected)

    def test_read_db_default_values(self):
        # Read database 1, which has a default initialization of all zeroes
        db_data = self.client.db_read(1, 0, 2)

        self.assertSequenceEqual(db_data, [0, 0])

    def test_read_db_initialized_values(self):
        # Read database 2, which has configured initial values (1, 0 ,- ,1)
        db_data = self.client.db_read(2, 0, 4)

        self.assertSequenceEqual(db_data, [1, 0, 0, 1])

    def test_read_db_out_of_range_values(self):
        size = self.snap7_instance.event_handler.dbs['s7comm_db1']['size']
        with self.assertRaises(Snap7Exception):
            self.client.db_read(1, 0, size + 1)

    def test_write_read_db(self):
        expected = [1, 0]
        self.client.db_write(1, 1, bytearray([0]))
        self.client.db_write(1, 0, bytearray([1]))
        db_data = self.client.db_read(1, 0, 2)
        output_list = []
        for data in db_data:
            output_list.append(data)
        self.assertSequenceEqual(output_list, expected)
