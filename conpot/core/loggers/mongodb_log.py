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

from pymongo import MongoClient


class MongodbLogger(object):

    def __init__(self, host, port, db_name, collection_name, sensor_id):
        port = int(port)
        client = MongoClient(host, port)
        db = client.get_database(db_name)
        self.collection = db.get_collection(collection_name)
        self.sensor_id = sensor_id

    def log(self, event):
        event['sensor_id'] = self.sensor_id
        processed_event = event.copy()
        processed_event['timestamp'] = processed_event['timestamp'].isoformat()
        del processed_event['id']
        self.collection.insert_one(processed_event)

    def log_session(self, session):
        pass
