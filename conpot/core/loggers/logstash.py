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

import logging
import socket
import json

logger = logging.getLogger(__name__)


class Logstash(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def log(self, data):
        processed_data = data.copy()
        processed_data['timestamp'] = processed_data['timestamp'].isoformat()
        del processed_data['id']

        report_string = json.dumps(processed_data)
        logging.debug("Sending to logstash: " + report_string)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            # Logstash needs a linebreak after the json string
            # Added here so it doesn't break in the middle of logging.debug() above
            sock.sendall(report_string + "\n")
            sock.close()
        except:
            message = "Unable to send to logstash."
            logging.exception(message)
            return message

    def log_session(self, session):
        pass
