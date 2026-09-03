from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings

client: MongoClient = MongoClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5000,
)

database: Database = client[settings.mongodb_database]


def get_database() -> Database:
    return database


def check_database_connection() -> bool:
    client.admin.command("ping")
    return True