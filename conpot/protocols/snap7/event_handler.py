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
from .event_data_constructor import EventDataConstructor

logger = logging.getLogger(__name__)


class EventHandler(object):
    def __init__(self, dbs, filters):
        self.data_bus = conpot_core.get_databus()
        self.dbs = dbs
        self.ignored_events = filters
        self.edc = EventDataConstructor(dbs)

        self._set_initial_values()

    def callbacks(self, event):
        construct_data = self.edc.cb_func_map.get(event.EvtCode, None)
        if construct_data:
            self._handle_logging(event, construct_data(event))

    def read_callbacks(self, event):
        """Is called BEFORE reading the data"""
        construct_data = self.edc.read_cb_func_map.get(event.EvtCode, None)
        if construct_data:
            self._handle_logging(event, construct_data(event))

    def _set_initial_values(self):
        for key in self.dbs.keys():
            # Always initialize all values with 0
            self.data_bus.set_value(key, [0] * self.dbs[key]['size'])
            # Replace with manually set values
            if 'initial' in self.dbs[key]:
                for x in range(len(self.dbs[key]['initial'])):
                    if self.dbs[key]['initial'][x] != '-':
                        self.data_bus.get_value(key)[x] = int(self.dbs[key]['initial'][x])

    @staticmethod
    def _parse_remote_ip(not_parsed_remote_ip):
        remote_ip_as_list = [str(not_parsed_remote_ip >> shift_amount & 0xFF) for shift_amount in (0, 8, 16, 24)]
        remote_ip = ".".join(remote_ip_as_list)
        return remote_ip

    @staticmethod
    def _new_session_event(remote_ip, data):
        session = conpot_core.get_session('snap7', remote_ip, None)
        session.add_event(data)
        return session.id

    def _handle_logging(self, event, data):
        if not self.check_if_ignored(event):
            remote_ip = self._parse_remote_ip(event.EvtSender)
            self._new_session_event(remote_ip, data)

    def check_if_ignored(self, event):
        event_fields = {
            'EvtSender': event.EvtSender,
            'EvtCode': event.EvtCode,
            'EvtRetCode': event.EvtRetCode,
            'EvtParam1': event.EvtParam1,
            'EvtParam2': event.EvtParam2,
            'EvtParam3': event.EvtParam3,
            'EvtParam4': event.EvtParam4
        }

        for ignored_event in self.ignored_events:
            match = None
            for event_field in event_fields.keys():
                if event_field in ignored_event.keys() and ignored_event[event_field] != event_fields[event_field]:
                    match = False
            if match is False:
                continue
            else:
                return True
        return False
