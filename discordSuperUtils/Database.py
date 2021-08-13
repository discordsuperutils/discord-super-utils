import os
import pymongo.database
import sqlite3
import psycopg2.extensions


class UnsupportedDatabase(Exception):
    """Raises error when the user tries to use an unsupported database."""


class _MongoDatabase:
    def __init__(self, database: pymongo.database.Database):
        self.database = database

    def __str__(self):
        return f"<DATABASE '{self.name}'>"

    def __repr__(self):
        return f"<DATABASE {self.name}, SIZE={self.size}, TABLES={', '.join(self.tables)}>"

    @property
    def size(self):
        return self.database.command('dbstats')['dataSize']

    @property
    def tables(self):
        return self.database.list_collection_names()

    @property
    def name(self):
        return self.database.name

    def insertifnotexists(self, data, table_name, checks):
        response = self.select([], table_name, checks, True)

        if not response:
            return self.insert(data, table_name)

    def insert(self, data, table_name):
        return self.database[table_name].insert_one(data)

    def create_table(self, table_name, columns=None, exists=False):
        if exists and table_name in self.tables:
            return

        return self.database.create_collection(table_name)

    def update(self, data, table_name, checks):
        return self.database[table_name].update_one(checks, {"$set": data})

    def updateorinsert(self, data, table_name, checks, insert_data):
        response = self.select([], table_name, checks, True)

        if len(response) == 1:
            return self.update(data, table_name, checks)

        return self.insert(insert_data, table_name)

    def delete(self, table_name, checks=None):
        return self.database[table_name].delete_one({} if checks is None else checks)

    def select(self, keys, table_name, checks, fetchall=False):
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


class _SqlDatabase:
    def __str__(self):
        return f"<SQL DATABASE>"

    def __with_commit(func):
        def inner(self, *args, **kwargs):
            resp = func(self, *args, **kwargs)
            self.commit()

            return resp

        return inner

    def __with_cursor(func):
        def inner(self, *args, **kwargs):
            cursor = self.database.cursor()
            resp = func(self, cursor, *args, **kwargs)
            cursor.close()

            return resp

        return inner

    def __init__(self, database):
        self.database = database
        self.place_holder = DATABASE_TYPES[type(database)]["placeholder"]

    def commit(self):
        self.database.commit()

    def close(self):
        self.database.close()

    def insertifnotexists(self, data, table_name, checks):
        response = self.select([], table_name, checks, True)

        if not response:
            return self.insert(data, table_name)

    @__with_cursor
    @__with_commit
    def insert(self, cursor, data, table_name):
        query = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join([self.place_holder] * len(data.values()))})"
        cursor.execute(query, list(data.values()))

    @__with_cursor
    @__with_commit
    def create_table(self, cursor, table_name, columns=None, exists=False):
        query = f'CREATE TABLE {"IF NOT EXISTS" if exists else ""} \"{table_name}\" ('

        for column in [] if columns is None else columns:
            query += f"\n\"{column['name']}\" {column['type']},"
        query = query[:-1]

        query += "\n);"
        cursor.execute(query)

    @__with_cursor
    @__with_commit
    def update(self, cursor, data, table_name, checks):
        query = f"UPDATE {table_name} SET "

        if data:
            for key in data:
                query += f"{key} = {self.place_holder}, "
            query = query[:-2]

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{check} = {self.place_holder} AND "

            query = query[:-4]

        cursor.execute(query, list(data.values()) + list(checks.values()))

    def updateorinsert(self, data, table_name, checks, insert_data):
        response = self.select([], table_name, checks, True)

        if len(response) == 1:
            return self.update(data, table_name, checks)

        return self.insert(insert_data, table_name)

    @__with_cursor
    @__with_commit
    def delete(self, cursor, table_name, checks=None):
        checks = {} if checks is None else checks

        query = f"DELETE FROM {table_name} "

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{list(check)[0]} = {self.place_holder} AND "

            query = query[:-4]

        values = [list(x.values())[0] for x in checks]
        cursor.execute(query, values)

    @__with_cursor
    def select(self, cursor, keys, table_name, checks, fetchall=False):
        keys = '*' if not keys else keys
        query = f"SELECT {','.join(keys)} FROM {table_name} "

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{check} = {self.place_holder} AND "

            query = query[:-4]

        cursor.execute(query, list(checks.values()))
        columns = [x[0] for x in cursor.description]

        return [dict(zip(columns, x)) for x in cursor.fetchall()] if fetchall else dict(zip(columns, cursor.fetchone()))


DATABASE_TYPES = {
    pymongo.database.Database: {"class": _MongoDatabase, "placeholder": None},
    sqlite3.Connection: {"class": _SqlDatabase, "placeholder": '?'},
    psycopg2.extensions.connection: {"class": _SqlDatabase, "placeholder": '%s'}
}


class DatabaseManager:
    """
    A database class for easier access
    database MUST be of type sqlite3 or mongodb
    """

    @staticmethod
    def connect(database):
        if type(database) not in DATABASE_TYPES:
            raise UnsupportedDatabase(f"Database of type {type(database)} is not supported by the database manager.")

        return DATABASE_TYPES[type(database)]["class"](database)