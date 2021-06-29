import os


class DatabaseManager:
    """
    A database class for easier access
    database MUST be of type sqlite3
    """

    def __str__(self):
        return f"<DATABASE '{self.name}'>"

    def __repr__(self):
        return f"<DATABASE {self.name}, PATH={self.path}, SIZE={self.size}, TABLES={', '.join(self.tables)}>"

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

    def commit(self):
        self.database.commit()

    def close(self):
        self.database.close()

    @property
    def size(self):
        return os.stat(self.path).st_size

    @property
    @__with_cursor
    def tables(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        return [x[0] for x in cursor.fetchall()]

    @property
    @__with_cursor
    def name(self, cursor):
        cursor.execute("PRAGMA database_list")
        return cursor.fetchall()[0][1]

    @property
    @__with_cursor
    def path(self, cursor):
        cursor.execute("PRAGMA database_list")
        return cursor.fetchall()[0][2]

    def insertifnotexists(self, keys, values, table_name, checks):
        response = self.select([], table_name, checks, True)

        if len(response) == 0:
            self.insert(keys, values, table_name)

    @__with_cursor
    @__with_commit
    def insert(self, cursor, keys, values, table_name):
        query = f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({', '.join(['?'] * len(values))})"
        cursor.execute(query, values)

    @__with_cursor
    @__with_commit
    def createtable(self, cursor, table_name, columns, exists=False):
        query = f'CREATE TABLE {"IF NOT EXISTS" if exists else ""} {table_name} ('

        for column in columns:
            query += f"\n{column['name']} {column['type']},"
        query = query[:-1]

        query += "\n)"

        cursor.execute(query)

    @__with_cursor
    @__with_commit
    def update(self, cursor, keys, values, table_name, checks):
        query = f"UPDATE {table_name} SET "

        if keys:
            for key in keys:
                query += f"{key} = ?, "
            query = query[:-2]

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{list(check)[0]} = ? AND "

            query = query[:-4]

        values += [list(x.values())[0] for x in checks]
        cursor.execute(query, values)

    def updateorinsert(self, keys, values, table_name, checks, insertkeys, insertvalues):
        response = self.select([], table_name, checks, True)

        if len(response) == 1:
            self.update(keys, values, table_name, checks)
        else:
            self.insert(insertkeys, insertvalues, table_name)

    @__with_cursor
    @__with_commit
    def delete(self, cursor, table_name, checks):
        query = f"DELETE FROM {table_name} "

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{list(check)[0]} = ? AND "

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
                query += f"{list(check)[0]} = ? AND "

            query = query[:-4]

        values = [list(x.values())[0] for x in checks]
        cursor.execute(query, values)

        return cursor.fetchall() if fetchall else cursor.fetchone()
