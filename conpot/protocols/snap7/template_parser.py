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
from lxml import etree
import socket
import struct
import logging

logger = logging.getLogger(__name__)


def _get_szl_id(ssl_part):
    id_as_string_of_two_hex = ssl_part.attrib['id']
    id_as_list_of_two_int = [int(id_as_string_of_two_hex[:2], 16), int(id_as_string_of_two_hex[2:], 16)]
    return id_as_list_of_two_int


def _format_for_szl(some_string, padding_limit):
    szl_part_name = []
    for char in some_string:
        szl_part_name.append(ord(char))
    while len(szl_part_name) < padding_limit:
        szl_part_name.append(0)
    return szl_part_name


class TemplateParser(object):
    def __init__(self, template):
        self.dom = etree.parse(template)
        self.data_bus = conpot_core.get_databus()

    def parse_db(self):
        databases = self.dom.xpath('//snap7/databases/*')
        dbs = {}
        for database in databases:
            db_name = database.attrib['name']
            dbs[db_name] = {}
            dbs[db_name]['size'] = int(database.xpath('./size/text()')[0])
            dbs[db_name]['index'] = int(database.xpath('./index/text()')[0])
            initial_values = database.xpath('./initial/text()')
            if len(initial_values) != 0:
                dbs[db_name]['initial'] = [value.strip() for value in initial_values[0].split(',')]
            dbs[db_name]['retentive'] = True if database.attrib.get('retentive') == "true" else False
        return dbs

    def parse_szl(self):
        system_status_lists = self.dom.xpath('//snap7/system_status_lists/*')
        szls = {}
        for ssl in system_status_lists:

            ssl_name = ssl.attrib['name']
            ssls_id = ssl.attrib['id']
            szls[ssls_id] = {}

            if ssl_name == "Module Identification":
                self._init_module_identification_szls(szls, ssl, ssls_id)
            elif ssl_name == "Component Identification":
                self._init_component_identification_szls(szls, ssl, ssls_id)
        return szls

    @staticmethod
    def _ip_to_int(ip):
        return struct.unpack("<L", socket.inet_aton(ip))[0]  # Little-endian comes from Snap7

    def parse_event_filters(self):
        event_filters = self.dom.xpath('//snap7/event_filters/*')
        filters_list = []
        for event_filter in event_filters:
            filters_list.append({})
            filter_fields = ['EvtSender.ip', 'EvtCode', 'EvtRetCode', 'EvtParam1', 'EvtParam2', 'EvtParam3', 'EvtParam4']
            for field_name in filter_fields:
                field_content = event_filter.xpath('./'+field_name+'/text()')
                if bool(field_content):
                    if field_name == 'EvtSender.ip':
                        filters_list[-1][field_name] = self._ip_to_int(field_content[0])
                    else:
                        filters_list[-1][field_name] = int(field_content[0])
        logger.debug("Event-Filters: %s" % filters_list)
        return filters_list

    def _init_module_identification_szls(self, szls, ssl, ssls_id):
        for ssl_part in ssl.xpath('./*'):
            tag = ssl_part.tag
            szls[ssls_id][tag] = {}

            description_element = ssl_part[0]
            szls[ssls_id][tag]['text'] = self._get_szl_description(description_element, 20)
            szls[ssls_id][tag]['id'] = _get_szl_id(ssl_part)

            raw_version = ssl_part[1].xpath('./text()')[0]
            version_databus = self.data_bus.get_value(raw_version)
            szls[ssls_id][tag]['version'] = [int(v) for v in version_databus.split('.')]

    def _init_component_identification_szls(self, szls, ssl, ssls_id):
        for ssl_part in ssl.xpath('./*'):
            tag = ssl_part.tag
            szls[ssls_id][tag] = {}

            szls[ssls_id][tag]['text'] = self._get_szl_description(ssl_part, 32)
            szls[ssls_id][tag]['id'] = _get_szl_id(ssl_part)

    def _get_szl_description(self, ssl_part, padding):
        szl_description_template_key = ssl_part.xpath('./text()')[0]
        szl_description = self.data_bus.get_value(szl_description_template_key)
        formatted_szl_description = _format_for_szl(szl_description, padding)
        return formatted_szl_description
