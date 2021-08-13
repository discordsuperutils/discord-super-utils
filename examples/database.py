import discordSuperUtils
import pymongo
import sqlite3

mongo_database = discordSuperUtils.DatabaseManager(pymongo.MongoClient("connection string")["DATABASENAME"])
sqlite_database = discordSuperUtils.DatabaseManager(sqlite3.connect("database"))

values = sqlite_database.insert({"guild": ..., "member": ...}, "table")
print(values)