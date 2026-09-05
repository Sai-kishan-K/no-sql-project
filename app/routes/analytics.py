from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import database


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def registrations_by_category():
    pipeline = [
        {
            "$project": {
                "category": 1,
                "confirmedRegistrations": {
                    "$size": {
                        "$filter": {
                            "input": "$registrations",
                            "as": "registration",
                            "cond": {
                                "$eq": [
                                    "$$registration.status",
                                    "confirmed",
                                ]
                            },
                        }
                    }
                },
            }
        },
        {
            "$group": {
                "_id": "$category",
                "eventCount": {
                    "$sum": 1,
                },
                "confirmedRegistrations": {
                    "$sum": "$confirmedRegistrations",
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "eventCount": 1,
                "confirmedRegistrations": 1,
            }
        },
        {
            "$sort": {
                "confirmedRegistrations": -1,
                "category": 1,
            }
        },
    ]

    return list(
        database.events.aggregate(pipeline)
    )


def top_five_events():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "category": 1,
                "capacity": 1,
                "confirmedRegistrations": {
                    "$size": {
                        "$filter": {
                            "input": "$registrations",
                            "as": "registration",
                            "cond": {
                                "$eq": [
                                    "$$registration.status",
                                    "confirmed",
                                ]
                            },
                        }
                    }
                },
            }
        },
        {
            "$project": {
                "title": 1,
                "category": 1,
                "capacity": 1,
                "confirmedRegistrations": 1,
                "occupancyPercentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$confirmedRegistrations",
                                        "$capacity",
                                    ]
                                },
                                100,
                            ]
                        },
                        2,
                    ]
                },
            }
        },
        {
            "$sort": {
                "confirmedRegistrations": -1,
                "title": 1,
            }
        },
        {
            "$limit": 5,
        },
    ]

    return list(
        database.events.aggregate(pipeline)
    )


def users_without_registrations():
    pipeline = [
        {
            "$lookup": {
                "from": "events",
                "localField": "_id",
                "foreignField": "registrations.userId",
                "as": "registeredEvents",
            }
        },
        {
            "$match": {
                "registeredEvents": {
                    "$size": 0,
                }
            }
        },
        {
            "$project": {
                "_id": 1,
                "firstName": 1,
                "lastName": 1,
                "email": 1,
                "department": 1,
                "role": 1,
            }
        },
        {
            "$sort": {
                "lastName": 1,
                "firstName": 1,
            }
        },
    ]

    return list(
        database.users.aggregate(pipeline)
    )


def events_above_average_occupancy():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "category": 1,
                "capacity": 1,
                "confirmedRegistrations": {
                    "$size": {
                        "$filter": {
                            "input": "$registrations",
                            "as": "registration",
                            "cond": {
                                "$eq": [
                                    "$$registration.status",
                                    "confirmed",
                                ]
                            },
                        }
                    }
                },
            }
        },
        {
            "$project": {
                "title": 1,
                "category": 1,
                "capacity": 1,
                "confirmedRegistrations": 1,
                "occupancyPercentage": {
                    "$multiply": [
                        {
                            "$divide": [
                                "$confirmedRegistrations",
                                "$capacity",
                            ]
                        },
                        100,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": None,
                "averageOccupancy": {
                    "$avg": "$occupancyPercentage",
                },
                "events": {
                    "$push": "$$ROOT",
                },
            }
        },
        {
            "$unwind": "$events"
        },
        {
            "$match": {
                "$expr": {
                    "$gt": [
                        "$events.occupancyPercentage",
                        "$averageOccupancy",
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": "$events._id",
                "title": "$events.title",
                "category": "$events.category",
                "capacity": "$events.capacity",
                "confirmedRegistrations": (
                    "$events.confirmedRegistrations"
                ),
                "occupancyPercentage": {
                    "$round": [
                        "$events.occupancyPercentage",
                        2,
                    ]
                },
                "averageOccupancy": {
                    "$round": [
                        "$averageOccupancy",
                        2,
                    ]
                },
            }
        },
        {
            "$sort": {
                "occupancyPercentage": -1,
                "title": 1,
            }
        },
    ]

    return list(
        database.events.aggregate(pipeline)
    )


def most_used_tags():
    pipeline = [
        {
            "$unwind": "$tags"
        },
        {
            "$group": {
                "_id": "$tags",
                "eventCount": {
                    "$sum": 1,
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "tag": "$_id",
                "eventCount": 1,
            }
        },
        {
            "$sort": {
                "eventCount": -1,
                "tag": 1,
            }
        },
    ]

    return list(
        database.events.aggregate(pipeline)
    )


def events_by_month():
    pipeline = [
        {
            "$project": {
                "month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$startDate",
                    }
                },
                "registrationCount": {
                    "$size": "$registrations",
                },
            }
        },
        {
            "$group": {
                "_id": "$month",
                "eventCount": {
                    "$sum": 1,
                },
                "registrationCount": {
                    "$sum": "$registrationCount",
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "month": "$_id",
                "eventCount": 1,
                "registrationCount": 1,
            }
        },
        {
            "$sort": {
                "month": 1,
            }
        },
    ]

    return list(
        database.events.aggregate(pipeline)
    )


@router.get("", response_class=HTMLResponse)
def analytics_page(request: Request):
    category_results = registrations_by_category()
    popular_events = top_five_events()
    users_without_events = users_without_registrations()
    above_average_events = (
        events_above_average_occupancy()
    )
    tag_results = most_used_tags()
    monthly_results = events_by_month()

    average_occupancy = 0

    if above_average_events:
        average_occupancy = above_average_events[
            0
        ].get("averageOccupancy", 0)

    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "page_title": "Analytics",
            "active_page": "analytics",
            "category_results": category_results,
            "popular_events": popular_events,
            "users_without_events": users_without_events,
            "above_average_events": above_average_events,
            "average_occupancy": average_occupancy,
            "tag_results": tag_results,
            "monthly_results": monthly_results,
        },
    )
