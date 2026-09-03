from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import CollectionInvalid

from app.config import settings


client = MongoClient(settings.mongodb_uri)
database = client[settings.mongodb_database]


users_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "firstName",
            "lastName",
            "email",
            "department",
            "role",
            "interests",
            "createdAt",
        ],
        "properties": {
            "firstName": {
                "bsonType": "string",
                "minLength": 1,
            },
            "lastName": {
                "bsonType": "string",
                "minLength": 1,
            },
            "email": {
                "bsonType": "string",
                "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            },
            "department": {
                "bsonType": "string",
                "minLength": 1,
            },
            "role": {
                "enum": ["student", "staff", "organizer"],
            },
            "interests": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
            },
            "createdAt": {
                "bsonType": "date",
            },
        },
    }
}


events_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "title",
            "description",
            "category",
            "tags",
            "organizerId",
            "location",
            "startDate",
            "endDate",
            "capacity",
            "registrations",
            "createdAt",
            "updatedAt",
        ],
        "properties": {
            "title": {
                "bsonType": "string",
                "minLength": 1,
            },
            "description": {
                "bsonType": "string",
            },
            "category": {
                "bsonType": "string",
                "minLength": 1,
            },
            "tags": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string",
                },
            },
            "organizerId": {
                "bsonType": "objectId",
            },
            "location": {
                "bsonType": "object",
                "required": ["building", "room", "address"],
                "properties": {
                    "building": {
                        "bsonType": "string",
                    },
                    "room": {
                        "bsonType": "string",
                    },
                    "address": {
                        "bsonType": "string",
                    },
                },
            },
            "startDate": {
                "bsonType": "date",
            },
            "endDate": {
                "bsonType": "date",
            },
            "capacity": {
                "bsonType": "int",
                "minimum": 1,
            },
            "registrations": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": [
                        "userId",
                        "registeredAt",
                        "status",
                    ],
                    "properties": {
                        "userId": {
                            "bsonType": "objectId",
                        },
                        "registeredAt": {
                            "bsonType": "date",
                        },
                        "status": {
                            "enum": [
                                "confirmed",
                                "cancelled",
                                "waitlisted",
                            ],
                        },
                    },
                },
            },
            "createdAt": {
                "bsonType": "date",
            },
            "updatedAt": {
                "bsonType": "date",
            },
        },
    }
}


def create_or_update_collection(name: str, validator: dict) -> None:
    try:
        database.create_collection(
            name,
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
        print(f"Created collection: {name}")
    except CollectionInvalid:
        database.command(
            "collMod",
            name,
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
        print(f"Updated validation for collection: {name}")


def create_indexes() -> None:
    database.users.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="unique_user_email",
    )

    database.events.create_index(
        [("startDate", ASCENDING)],
        name="event_start_date",
    )

    database.events.create_index(
        [("category", ASCENDING)],
        name="event_category",
    )

    database.events.create_index(
        [("tags", ASCENDING)],
        name="event_tags",
    )

    database.events.create_index(
        [("organizerId", ASCENDING)],
        name="event_organizer",
    )

    database.events.create_index(
        [("category", ASCENDING), ("startDate", DESCENDING)],
        name="category_and_start_date",
    )

    print("Indexes created or already available.")


def initialize_database() -> None:
    client.admin.command("ping")
    print("Connected to MongoDB.")

    create_or_update_collection("users", users_validator)
    create_or_update_collection("events", events_validator)
    create_indexes()

    print(f"Database '{settings.mongodb_database}' initialized successfully.")
#asdasd

if __name__ == "__main__":
    initialize_database()