from const import *
from tinydb import TinyDB, where, Query
from datetime import datetime
import pickle
import os
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

tinyDB = TinyDB(DATABASE, storage=CachingMiddleware(JSONStorage))
device_cache = {}  # {session_id: Device}
closed_group_cache = {}  # {closed_group_id: ClosedGroup}


class DatabaseModel:
    def __init__(self, database, doc_id=None):
        self.database = database
        self.doc_id = doc_id

    def find(self, queries):
        final_query = None
        for query in queries:
            final_query = final_query & query if final_query else query
        if final_query:
            documents = self.database.search(final_query)
            if len(documents) > 0:
                self.doc_id = documents[0].doc_id
                self.from_mapping(documents[0])
                return True
        return False

    def from_mapping(self, mapping):
        pass

    def to_mapping(self):
        pass

    def save(self):
        mapping = self.to_mapping()
        if self.doc_id:
            self.database.update(mapping, doc_ids=[self.doc_id])
        else:
            self.doc_id = self.database.insert(mapping)


class Device(DatabaseModel):
    def __init__(self, doc_id=None, session_id=None, tokens=None):
        super().__init__(tinyDB.table(PUBKEY_TOKEN_TABLE), doc_id)
        if session_id:
            self.session_id = session_id
            documents = self.database.search(where(PUBKEY) == session_id)
            if len(documents) > 0:
                self.doc_id = documents[0].doc_id
        self.tokens = set(tokens) if tokens else set()

    def from_mapping(self, mapping):
        self.session_id = mapping[PUBKEY]
        self.tokens = set(mapping[TOKEN])

    def to_mapping(self):
        return {PUBKEY: self.session_id,
                TOKEN: list(self.tokens)}


class ClosedGroup(DatabaseModel):
    def __init__(self, doc_id=None, closed_group_id=None, members=None):
        super().__init__(tinyDB.table(CLOSED_GROUP_TABLE), doc_id)
        if closed_group_id:
            self.closed_group_id = closed_group_id
            documents = self.database.search(where(CLOSED_GROUP) == closed_group_id)
            if len(documents) > 0:
                self.doc_id = documents[0].doc_id
        self.members = set(members) if members else set()

    def from_mapping(self, mapping):
        self.closed_group_id = mapping[CLOSED_GROUP]
        self.members = set(mapping[MEMBERS])

    def to_mapping(self):
        return {CLOSED_GROUP: self.closed_group_id,
                MEMBERS: list(self.members)}


def load_cache():
    device_table = tinyDB.table(PUBKEY_TOKEN_TABLE)
    devices = device_table.all()
    for device_mapping in devices:
        device = Device()
        device.from_mapping(device_mapping)
        device_cache[device.session_id] = device

    closed_group_table = tinyDB.table(CLOSED_GROUP_TABLE)
    closed_groups = closed_group_table.all()
    for closed_group_mapping in closed_groups:
        closed_group = ClosedGroup()
        closed_group.from_mapping(closed_group_mapping)
        closed_group_cache[closed_group.closed_group_id] = closed_group


def migrate_database_if_needed():
    def migrate(old_db_name, new_table_name, json_structure):
        db_map = None
        if os.path.isfile(old_db_name):
            with open(old_db_name, 'rb') as old_db:
                db_map = dict(pickle.load(old_db))
            old_db.close()
        if db_map is not None and len(db_map) > 0:
            items = []
            for key, value in db_map.items():
                item = {}
                for key_name, value_name in json_structure.items():
                    item[key_name] = key
                    item[value_name] = list(value)
                items.append(item)
            tinyDB.table(new_table_name).insert_multiple(items)
            os.remove(old_db_name)

    migrate(PUBKEY_TOKEN_DB_V2, PUBKEY_TOKEN_TABLE, {PUBKEY: TOKEN})
    migrate(CLOSED_GROUP_DB, CLOSED_GROUP_TABLE, {CLOSED_GROUP: MEMBERS})


def store_data(last_statistics_date, now, ios_pn_number, android_pn_number, total_message_number):
    db = tinyDB.table(STATISTICS_TABLE)
    fmt = "%Y-%m-%d %H:%M:%S"
    db.insert({START_DATE: last_statistics_date.strftime(fmt),
               END_DATE: now.strftime(fmt),
               IOS_PN_NUMBER: ios_pn_number,
               ANDROID_PN_NUMBER: android_pn_number,
               TOTAL_MESSAGE_NUMBER: total_message_number})


def get_data(start_date, end_date):
    db = tinyDB.table(STATISTICS_TABLE)

    def try_to_convert_datetime(date_str):
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                pass

    def test_func(val, date_str, ascending):
        date_1 = try_to_convert_datetime(val)
        date_2 = try_to_convert_datetime(date_str)
        return date_1 > date_2 if ascending else date_1 < date_2

    data_query = Query()
    if start_date and end_date:
        return db.search(data_query[START_DATE].test(test_func, start_date, True) &
                         data_query[END_DATE].test(test_func, end_date, False))
    elif start_date:
        return db.search(data_query[START_DATE].test(test_func, start_date, True))
    else:
        return db.all()


def get_device(session_id):
    device = device_cache.get(session_id)
    if device is None:
        device = Device()
        if device.find([where(PUBKEY) == session_id]):
            device_cache[session_id] = device
        else:
            return None
    return device


def get_closed_group(closed_group_id):
    closed_group = closed_group_cache.get(closed_group_id)
    if closed_group is None:
        closed_group = ClosedGroup()
        if closed_group.find([where(CLOSED_GROUP) == closed_group_id]):
            closed_group_cache[closed_group_id] = closed_group
        else:
            return None
    return closed_group
