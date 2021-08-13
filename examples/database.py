import discordSuperUtils
from pymongo import MongoClient
import sqlite3
import psycopg2

postgre_database = discordSuperUtils.DatabaseManager.connect(psycopg2.connect(dbname="DATABASE NAME",
                                                                              user="postgres",
                                                                              password="x"))
mongo_database = discordSuperUtils.DatabaseManager.connect(MongoClient("connection string")["DATABASE NAME"])
sqlite_database = discordSuperUtils.DatabaseManager.connect(sqlite3.connect("database"))

values = sqlite_database.insert({"guild": ..., "member": ...}, "table")
print(values)
