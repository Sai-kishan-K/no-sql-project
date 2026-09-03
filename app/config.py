import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    mongodb_uri: str = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017",
    )
    mongodb_database: str = os.getenv(
        "MONGODB_DATABASE",
        "campus_events",
    )
    app_name: str = os.getenv(
        "APP_NAME",
        "Campus Events Manager",
    )
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()