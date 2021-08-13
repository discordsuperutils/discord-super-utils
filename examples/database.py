import discordSuperUtils
from pymongo import MongoClient
import sqlite3

mongo_database = discordSuperUtils.DatabaseManager.connect(MongoClient("connection string")["DATABASE NAME"])
sqlite_database = discordSuperUtils.DatabaseManager.connect(sqlite3.connect("database"))

values = sqlite_database.insert({"guild": ..., "member": ...}, "table")
print(values)