import os
from enum import Enum
import pymongo.database
import sqlite3


class UnsupportedDatabase(Exception):
    """Raises error when the user tries to use an unsupported database."""


class DatabaseTypes(Enum):
    SQLITE = sqlite3.Connection
    MONGO = pymongo.database.Database


DATABASE_CONFIG = {
    DatabaseTypes.SQLITE: {"cursor": True, "commit": True, "SQL": True},
    DatabaseTypes.MONGO: {"cursor": False, "commit": False, "SQL": False}
}


class DatabaseManager:
    """
    A database class for easier access
    database MUST be of type sqlite3 or mongodb
    """

    def __str__(self):
        return f"<DATABASE '{self.name}'>"

    def __repr__(self):
        return f"<DATABASE {self.name}, PATH={self.path}, SIZE={self.size}, TABLES={', '.join(self.tables)}>"

    def __with_commit(func):
        def inner(self, *args, **kwargs):
            resp = func(self, *args, **kwargs)
            if DATABASE_CONFIG[self.database_type]["commit"]:
                self.commit()

            return resp

        return inner

    def __with_cursor(func):
        def inner(self, *args, **kwargs):
            if DATABASE_CONFIG[self.database_type]["cursor"]:
                cursor = self.database.cursor()
                resp = func(self, cursor, *args, **kwargs)
                cursor.close()
            else:
                resp = func(self, None, *args, **kwargs)

            return resp

        return inner

    def __init__(self, database):
        self.database = database
        if type(self.database) not in [e.value for e in DatabaseTypes]:
            raise UnsupportedDatabase(f"Database of type {type(database)} is not supported by the database manager.")

        self.database_type = DatabaseTypes(type(database))

    def commit(self):
        if DATABASE_CONFIG[self.database_type]["commit"]:
            self.database.commit()

    def close(self):
        self.database.close()

    @property
    def size(self):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            return os.stat(self.path).st_size
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database.command('dbstats')['dataSize']

    @property
    @__with_cursor
    def tables(self, cursor):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            return [x[0] for x in cursor.fetchall()]
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database.list_collection_names()

    @property
    @__with_cursor
    def name(self, cursor):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            cursor.execute("PRAGMA database_list")
            return cursor.fetchall()[0][1]
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database.name

    @property
    @__with_cursor
    def path(self, cursor):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            cursor.execute("PRAGMA database_list")
            return cursor.fetchall()[0][2]
        elif self.database_type == DatabaseTypes.MONGO:
            return None

    def insertifnotexists(self, data, table_name, checks):
        response = self.select([], table_name, checks, True)

        if not response:
            return self.insert(data, table_name)

    @__with_cursor
    @__with_commit
    def insert(self, cursor, data, table_name):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            query = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join(['?'] * len(data.values()))})"
            cursor.execute(query, list(data.values()))
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database[table_name].insert_one(data)

    @__with_cursor
    @__with_commit
    def create_table(self, cursor, table_name, columns=None, exists=False):
        columns = [] if columns is None else columns

        if DATABASE_CONFIG[self.database_type]["SQL"]:
            query = f'CREATE TABLE {"IF NOT EXISTS" if exists else ""} {table_name} ('

            for column in columns:
                query += f"\n{column['name']} {column['type']},"
            query = query[:-1]

            query += "\n)"

            cursor.execute(query)
        elif self.database_type == DatabaseTypes.MONGO:
            if exists and table_name in self.tables:
                return

            return self.database.create_collection(table_name)

    @__with_cursor
    @__with_commit
    def update(self, cursor, data, table_name, checks):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            query = f"UPDATE {table_name} SET "

            if data:
                for key in data:
                    query += f"{key} = ?, "
                query = query[:-2]

            if checks:
                query += "WHERE "
                for check in checks:
                    query += f"{check} = ? AND "

                query = query[:-4]

            cursor.execute(query, list(data.values() + checks.values()))
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database[table_name].update_one(checks, {"$set": data})

    def updateorinsert(self, data, table_name, checks, insert_data):
        response = self.select([], table_name, checks, True)

        if len(response) == 1:
            return self.update(data, table_name, checks)
        else:
            return self.insert(insert_data, table_name)

    @__with_cursor
    @__with_commit
    def delete(self, cursor, table_name, checks=None):
        checks = {} if checks is None else checks

        if DATABASE_CONFIG[self.database_type]["SQL"]:
            query = f"DELETE FROM {table_name} "

            if checks:
                query += "WHERE "
                for check in checks:
                    query += f"{list(check)[0]} = ? AND "

                query = query[:-4]

            values = [list(x.values())[0] for x in checks]
            cursor.execute(query, values)
        elif self.database_type == DatabaseTypes.MONGO:
            return self.database[table_name].delete_one(checks)

    @__with_cursor
    def select(self, cursor, keys, table_name, checks, fetchall=False):
        if DATABASE_CONFIG[self.database_type]["SQL"]:
            keys = '*' if not keys else keys
            query = f"SELECT {','.join(keys)} FROM {table_name} "

            if checks:
                query += "WHERE "
                for check in checks:
                    query += f"{check} = ? AND "

                query = query[:-4]

            cursor.execute(query, list(checks.values()))
            columns = [x[0] for x in cursor.description]

            return [dict(zip(columns, x)) for x in cursor.fetchall()] if fetchall else dict(zip(columns, cursor.fetchone()))
        elif self.database_type == DatabaseTypes.MONGO:
            if fetchall:
                fetch = list(self.database[table_name].find(checks))
                result = []

                for doc in fetch:
                    current_doc = {}

                    for key, value in doc.items():
                        if not keys or key in keys:
                            current_doc[key] = value

                    result.append(current_doc)
            else:
                fetch = self.database[table_name].find_one(checks)
                result = {}

                if fetch is not None:
                    for key, value in fetch.items():
                        if not keys or key in keys:
                            result[key] = value
                else:
                    result = None

            return result