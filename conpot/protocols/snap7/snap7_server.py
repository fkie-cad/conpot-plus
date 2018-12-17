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
import time
import logging
import snap7
from conpot.protocols.snap7.event_handler import EventHandler
from conpot.protocols.snap7.template_parser import TemplateParser
from conpot.protocols.snap7.szl_creator import SZLCreator

import signal

logger = logging.getLogger(__name__)


class Snap7Server(object):
    def __init__(self, template, template_directory, args):
        self.server = None

        template_parser = TemplateParser(template)
        self.dbs = template_parser.parse_db()
        custom_szl_data = template_parser.parse_szl()
        self.filters = template_parser.parse_event_filters()

        self.szl_creator = SZLCreator(custom_szl_data)

        self.data_bus = conpot_core.get_databus()
        self.event_handler = EventHandler(self.dbs, self.filters)

        signal.signal(signal.SIGINT, self._server_stopper)
        signal.signal(signal.SIGTERM, self._server_stopper)

    @staticmethod
    def _server_stopper(signum, handler):
        exit()  # Workaround to stop Conpot ...

    @staticmethod
    def _setup_modified_snap7_logging():
        snap7.server.logger.propagate = False

        log_formatter = logging.Formatter('%(asctime)s Snap7 - %(message)s')

        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        snap7.server.logger.addHandler(log_handler)

    def _register_dbs_in_snap7(self):
        for db_name in self.dbs.keys():
            db_size = self.dbs[db_name]['size']
            snap7_byte = snap7.snap7types.wordlen_to_ctypes[snap7.snap7types.S7WLByte]
            self.dbs[db_name]['data'] = (snap7_byte * db_size)()

            db_index = self.dbs[db_name]['index']
            self.server.register_area(snap7.snap7types.srvAreaDB, db_index, self.dbs[db_name]['data'])

    def _setup_server(self):
        self._setup_modified_snap7_logging()

        self.server = snap7.server.Server()

        self.server.set_events_callback(self.event_handler.callbacks)
        self.server.set_read_events_callback(self.event_handler.read_callbacks)

        self._register_dbs_in_snap7()
        self.szl_creator.set_custom_identification_szls(self.server)

    def _pick_events(self):
        while True:
            while True:
                if not self.server.pick_event():
                    break
            time.sleep(1)

    def start(self, host, port):
        self._setup_server()
        self.server.start(tcpport=port)
        logger.info('snap7 server started on: {0}'.format((host, port)))

        self._pick_events()

    def stop(self):
        self.server.stop()
