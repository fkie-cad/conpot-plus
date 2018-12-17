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


class EventDataConstructor(object):
    def __init__(self, dbs):
        self.data_bus = conpot_core.get_databus()
        self.dbs = dbs

        self.cb_func_map = {
            0x00000001: self._construct_server_stopped_data,
            0x00000002: self._construct_server_stopped_data,
            0x00000004: self._construct_listener_cannot_start_data,
            0x00000008: self._construct_client_added_data,
            0x00000010: self._construct_client_rejected_data,
            0x00000020: self._construct_client_no_room_data,
            0x00000040: self._construct_client_exception_data,
            0x00000080: self._construct_client_disconnected_data,
            0x00000100: self._construct_client_terminated_data,
            0x00000200: self._construct_client_dropped_data,
            0x00040000: self._construct_write_db_data,
            0x00010000: self._construct_get_pdu_incoming_data,
            0x00080000: self._construct_get_pdu_size_data,
            0x00100000: self._construct_read_szl_request_data,
            0x00200000: self._construct_clock_data,
            0x00400000: self._construct_upload_data,
            0x00800000: self._construct_download_data,
            0x01000000: self._construct_directory_data,
            0x02000000: self._construct_security_data,
            0x04000000: self._construct_control_data,
            0x08000000: self._construct_group_programmer_data,
            0x10000000: self._construct_group_cyclic_data_data
        }

        self.read_cb_func_map = {
            0x00020000: self._construct_read_db_data
        }

    def _construct_server_started_data(self, _):
        return {'type': 'SERVER_STARTED'}

    def _construct_server_stopped_data(self, _):
        return {'type': 'SERVER_STOPPED'}

    def _construct_listener_cannot_start_data(self, _):
        return {'type': 'LISTENER_CANNOT_START'}

    def _construct_client_added_data(self, _):
        return {'type': 'CLIENT_ADDED'}

    def _construct_client_rejected_data(self, _):
        return {'type': 'CLIENT_REJECTED'}

    def _construct_client_no_room_data(self, _):
        return {'type': 'CLIENT_NO_ROOM'}

    def _construct_client_exception_data(self, _):
        return {'type': 'CLIENT_EXCEPTION'}

    def _construct_client_disconnected_data(self, _):
        return {'type': 'CLIENT_DISCONNECTED'}

    def _construct_client_terminated_data(self, _):
        return {'type': 'CLIENT_TERMINATED'}

    def _construct_client_dropped_data(self, _):
        return {'type': 'CLIENT_DROPPED'}

    def _construct_write_db_data(self, event):
        db_address = event.EvtParam2
        db_key = "s7comm_db"+str(event.EvtParam2)
        cell_address = event.EvtParam3
        value = self.dbs[db_key]['data'][cell_address]

        # Write value to data_bus
        self.data_bus.get_value(db_key)[cell_address] = self.dbs[db_key]['data'][cell_address]

        data = {
            'type': 'WRITE_DB',
            'target_db': {
                'name': db_key,
                'db_address': db_address,
                'value': value,
                'cell_address': cell_address
            }
        }

        return data

    def _construct_get_pdu_incoming_data(self, event):
        pdu_size = event.EvtParam1

        data = {
            'type': 'PDU_INCOMING',
            'pdu_size': pdu_size
        }

        return data

    def _construct_get_pdu_size_data(self, event):
        pdu_size = event.EvtParam1

        data = {
            'type': 'GET_PDU_SIZE',
            'pdu_size': pdu_size
        }

        return data

    def _construct_read_szl_request_data(self, event):
        szl_id = event.EvtParam1
        szl_index = event.EvtParam2

        id_map = {
            0x424: 'CPU_RUNNING_STATE',
            0x1c: 'DEVICE_INFO',
            0x11: 'COMPONENT_IDENTIFICATION'
        }

        data = {
            'type': 'READ_SZL_REQUEST',
            'target_szl': {
                'id': szl_id,
                'index': szl_index
            },
            'sub_type': id_map.get(szl_id, 'UNCLASSIFIED_SZL_ID')
        }

        return data

    def _construct_clock_data(self, event):
        clock_code = event.EvtParam1

        code_map = {
            0x0000: 'UNKNOWN',
            0x0001: 'GET_CLOCK',
            0x0002: 'SET_CLOCK'
        }

        data = {
            'type': 'CLOCK',
            'clock_code': clock_code,
            'sub_type': code_map.get(clock_code, 'UNHANDLED')
        }

        return data

    def _construct_upload_data(self, event):
        block_type = event.EvtParam1
        block_number = event.EvtParam2

        data = {
            'type': 'UPLOAD',
            'block_type': block_type,
            'block_number': block_number
        }

        return data

    def _construct_download_data(self, event):
        block_type = event.EvtParam1
        block_number = event.EvtParam2
        block_length = event.EvtParam3

        data = {
            'type': 'DOWNLOAD',
            'block_type': block_type,
            'block_number': block_number,
            'block_length': block_length
        }

        return data

    def _construct_directory_data(self, event):
        logger.debug('Snap7 download event')
        directory_code = event.EvtParam1

        data = {
            'type': 'DIRECTORY',
            'directory_code': directory_code
        }

        if directory_code == 0x0000:
            data['sub_type'] = "UNKNOWN"
        elif directory_code == 0x0001:
            data['sub_type'] = "GET_BLOCK_LIST"
        elif directory_code == 0x0002:
            data['block_type'] = event.EvtParam2
            data['sub_type'] = "START_LIST_BOT"
        elif directory_code == 0x0003:
            data['block_type'] = event.EvtParam2
            data['sub_type'] = "LIST_BOT"
        elif directory_code == 0x0004:
            data['block_type_info'] = event.EvtParam2
            data['block_number'] = event.EvtParam3
            data['sub_type'] = "GET_BLOCK_INFO"

        return data

    def _construct_group_programmer_data(self, event):
        evs = event.EvtParam1

        data = {
            'type': 'GROUP_PROGRAMMER',
            'evs': evs
        }

        return data

    def _construct_group_cyclic_data_data(self, event):
        evs = event.EvtParam1

        data = {
            'type': 'GROUP_CYCLIC_DATA',
            'evs': evs
        }

        return data

    def _construct_security_data(self, event):
        logger.debug('Snap7 security event')
        security_code = event.EvtParam1

        code_map = {
            0x0000: 'UNKNOWN',
            0x0001: 'SET_PASSWORD',
            0x0002: 'CLEAR_PASSWORD'
        }

        data = {
            'type': 'SECURITY',
            'security_code': security_code,
            'sub_type': code_map.get(security_code, 'UNHANDLED')
        }

        return data

    def _construct_control_data(self, event):
        logger.debug('Snap7 control event')
        control_code = event.EvtParam1

        code_map = {
            0x0000: 'UNKNOWN',
            0x0001: 'COLD_START',
            0x0002: 'WARM_START',  # Not implemented in Snap7? Uses cold start instead
            0x0003: 'STOP'
        }

        data = {
            'type': 'CONTROL',
            'control_code': control_code,
            'sub_type': code_map.get(control_code, 'UNHANDLED')
        }

        return data

    def _construct_read_db_data(self, event):
        db_address = event.EvtParam2
        db_key = "s7comm_db"+str(db_address)
        start_addr = event.EvtParam3
        end_addr = event.EvtParam3 + event.EvtParam4
        read_values = []

        # Read the values
        for byte_addr in range(start_addr, end_addr):
            self.dbs[db_key]['data'][byte_addr] = ctypes.c_byte(self.data_bus.get_value(db_key)[byte_addr])
            read_values.append(self.dbs[db_key]['data'][byte_addr])

        data = {
            'type': 'READ_DB',
            'target_db': {
                'name': db_key,
                'db_address': db_address,
                'values': read_values,
                'start_cell_address': start_addr,
                'end_cell_address': end_addr
            }
        }

        return data
