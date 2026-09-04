import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from bson import ObjectId
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import ASCENDING, DESCENDING

from app.database import database


router = APIRouter(prefix="/events", tags=["Events"])

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def valid_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=404,
            detail="Invalid event identifier",
        )

    return ObjectId(value)


def redirect_with_message(
    message: str,
    message_type: str = "success",
) -> RedirectResponse:
    parameters = urlencode(
        {
            "message": message,
            "message_type": message_type,
        }
    )

    return RedirectResponse(
        url=f"/events?{parameters}",
        status_code=303,
    )


def parse_form_datetime(value: str) -> datetime:
    try:
        parsed_value = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Enter a valid date and time.") from exc

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=timezone.utc)

    return parsed_value


def prepare_event_form(
    event: Optional[dict] = None,
) -> dict:
    if not event:
        return {
            "title": "",
            "description": "",
            "category": "",
            "tagsText": "",
            "startDateInput": "",
            "endDateInput": "",
            "capacity": "",
            "building": "",
            "room": "",
            "address": "",
            "organizerId": "",
        }

    prepared_event = event.copy()

    prepared_event["tagsText"] = ", ".join(
        event.get("tags", [])
    )

    prepared_event["startDateInput"] = event[
        "startDate"
    ].strftime("%Y-%m-%dT%H:%M")

    prepared_event["endDateInput"] = event[
        "endDate"
    ].strftime("%Y-%m-%dT%H:%M")

    prepared_event["building"] = event.get(
        "location",
        {},
    ).get("building", "")

    prepared_event["room"] = event.get(
        "location",
        {},
    ).get("room", "")

    prepared_event["address"] = event.get(
        "location",
        {},
    ).get("address", "")

    prepared_event["organizerId"] = str(
        event.get("organizerId", "")
    )

    return prepared_event


def get_organizers() -> list:
    return list(
        database.users.find(
            {},
            {
                "firstName": 1,
                "lastName": 1,
                "email": 1,
                "role": 1,
            },
        ).sort(
            [
                ("lastName", ASCENDING),
                ("firstName", ASCENDING),
            ]
        )
    )


def validate_event_form(
    title: str,
    description: str,
    category: str,
    tags: str,
    start_date: str,
    end_date: str,
    capacity: int,
    building: str,
    room: str,
    address: str,
    organizer_id: str,
    current_registration_count: int = 0,
):
    errors = []

    title = title.strip()
    description = description.strip()
    category = category.strip()
    building = building.strip()
    room = room.strip()
    address = address.strip()

    tag_list = [
        tag.strip()
        for tag in tags.split(",")
        if tag.strip()
    ]

    if not title:
        errors.append("Title is required.")

    if not description:
        errors.append("Description is required.")

    if not category:
        errors.append("Category is required.")

    if not tag_list:
        errors.append("Add at least one tag.")

    if capacity < 1:
        errors.append("Capacity must be at least 1.")

    if capacity < current_registration_count:
        errors.append(
            "Capacity cannot be smaller than the current "
            "number of registrations."
        )

    if not building or not room or not address:
        errors.append(
            "Building, room, and address are required."
        )

    try:
        parsed_start_date = parse_form_datetime(start_date)
        parsed_end_date = parse_form_datetime(end_date)

        if parsed_end_date <= parsed_start_date:
            errors.append(
                "End date must be later than start date."
            )

    except ValueError:
        parsed_start_date = None
        parsed_end_date = None
        errors.append("Enter valid start and end dates.")

    if not ObjectId.is_valid(organizer_id):
        errors.append("Select a valid organizer.")
        organizer_object_id = None
    else:
        organizer_object_id = ObjectId(organizer_id)

        organizer_exists = database.users.count_documents(
            {"_id": organizer_object_id},
            limit=1,
        )

        if not organizer_exists:
            errors.append(
                "The selected organizer does not exist."
            )

    event_document = {
        "title": title,
        "description": description,
        "category": category,
        "tags": tag_list,
        "startDate": parsed_start_date,
        "endDate": parsed_end_date,
        "capacity": capacity,
        "location": {
            "building": building,
            "room": room,
            "address": address,
        },
        "organizerId": organizer_object_id,
    }

    return errors, event_document


@router.get("", response_class=HTMLResponse)
def list_events(
    request: Request,
    q: str = "",
    category: str = "",
    tag: str = "",
    status: str = "",
    sort: str = "date_asc",
    message: str = "",
    message_type: str = "success",
):
    conditions = []

    if q.strip():
        safe_search = re.escape(q.strip())

        conditions.append(
            {
                "$or": [
                    {
                        "title": {
                            "$regex": safe_search,
                            "$options": "i",
                        }
                    },
                    {
                        "description": {
                            "$regex": safe_search,
                            "$options": "i",
                        }
                    },
                ]
            }
        )

    if category:
        conditions.append({"category": category})

    if tag:
        # MongoDB automatically searches array elements.
        conditions.append({"tags": tag})

    now = datetime.now(timezone.utc)

    if status == "upcoming":
        conditions.append(
            {"startDate": {"$gte": now}}
        )
    elif status == "past":
        conditions.append(
            {"startDate": {"$lt": now}}
        )
    elif status == "available":
        conditions.append(
            {
                "$expr": {
                    "$lt": [
                        {"$size": "$registrations"},
                        "$capacity",
                    ]
                }
            }
        )

    mongo_query = (
        {"$and": conditions}
        if conditions
        else {}
    )

    sort_options = {
        "date_asc": [("startDate", ASCENDING)],
        "date_desc": [("startDate", DESCENDING)],
        "title_asc": [("title", ASCENDING)],
        "capacity_desc": [("capacity", DESCENDING)],
    }

    selected_sort = sort_options.get(
        sort,
        sort_options["date_asc"],
    )

    events = list(
        database.events.find(
            mongo_query,
            {
                "title": 1,
                "description": 1,
                "category": 1,
                "tags": 1,
                "startDate": 1,
                "endDate": 1,
                "capacity": 1,
                "location": 1,
                "organizerId": 1,
                "registrations": 1,
            },
        ).sort(selected_sort)
    )

    for event in events:
        event["registrationCount"] = len(
            event.get("registrations", [])
        )

        organizer = database.users.find_one(
            {"_id": event.get("organizerId")},
            {
                "firstName": 1,
                "lastName": 1,
            },
        )

        event["organizer"] = organizer
        event["isPast"] = event["startDate"] < now

    categories = database.events.distinct("category")
    tags = database.events.distinct("tags")

    categories.sort()
    tags.sort()

    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "page_title": "Events",
            "active_page": "events",
            "events": events,
            "categories": categories,
            "tags": tags,
            "filters": {
                "q": q,
                "category": category,
                "tag": tag,
                "status": status,
                "sort": sort,
            },
            "message": message,
            "message_type": message_type,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def create_event_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="event_form.html",
        context={
            "page_title": "Create Event",
            "active_page": "events",
            "form_heading": "Create Event",
            "form_action": "/events/new",
            "submit_label": "Create event",
            "event": prepare_event_form(),
            "organizers": get_organizers(),
            "errors": [],
        },
    )


@router.post("/new")
def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    tags: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    capacity: int = Form(...),
    building: str = Form(...),
    room: str = Form(...),
    address: str = Form(...),
    organizer_id: str = Form(...),
):
    errors, event_document = validate_event_form(
        title=title,
        description=description,
        category=category,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        capacity=capacity,
        building=building,
        room=room,
        address=address,
        organizer_id=organizer_id,
    )

    form_values = {
        "title": title,
        "description": description,
        "category": category,
        "tagsText": tags,
        "startDateInput": start_date,
        "endDateInput": end_date,
        "capacity": capacity,
        "building": building,
        "room": room,
        "address": address,
        "organizerId": organizer_id,
    }

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="event_form.html",
            context={
                "page_title": "Create Event",
                "active_page": "events",
                "form_heading": "Create Event",
                "form_action": "/events/new",
                "submit_label": "Create event",
                "event": form_values,
                "organizers": get_organizers(),
                "errors": errors,
            },
            status_code=400,
        )

    now = datetime.now(timezone.utc)

    event_document.update(
        {
            "registrations": [],
            "createdAt": now,
            "updatedAt": now,
        }
    )

    database.events.insert_one(event_document)

    return redirect_with_message(
        "Event created successfully."
    )


@router.get("/{event_id}/edit", response_class=HTMLResponse)
def edit_event_form(
    request: Request,
    event_id: str,
):
    object_id = valid_object_id(event_id)

    event = database.events.find_one(
        {"_id": object_id}
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="event_form.html",
        context={
            "page_title": "Edit Event",
            "active_page": "events",
            "form_heading": "Edit Event",
            "form_action": f"/events/{event_id}/edit",
            "submit_label": "Save changes",
            "event": prepare_event_form(event),
            "organizers": get_organizers(),
            "errors": [],
        },
    )


@router.post("/{event_id}/edit")
def update_event(
    request: Request,
    event_id: str,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    tags: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    capacity: int = Form(...),
    building: str = Form(...),
    room: str = Form(...),
    address: str = Form(...),
    organizer_id: str = Form(...),
):
    object_id = valid_object_id(event_id)

    existing_event = database.events.find_one(
        {"_id": object_id}
    )

    if not existing_event:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    registration_count = len(
        existing_event.get("registrations", [])
    )

    errors, event_document = validate_event_form(
        title=title,
        description=description,
        category=category,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        capacity=capacity,
        building=building,
        room=room,
        address=address,
        organizer_id=organizer_id,
        current_registration_count=registration_count,
    )

    form_values = {
        "_id": object_id,
        "title": title,
        "description": description,
        "category": category,
        "tagsText": tags,
        "startDateInput": start_date,
        "endDateInput": end_date,
        "capacity": capacity,
        "building": building,
        "room": room,
        "address": address,
        "organizerId": organizer_id,
    }

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="event_form.html",
            context={
                "page_title": "Edit Event",
                "active_page": "events",
                "form_heading": "Edit Event",
                "form_action": f"/events/{event_id}/edit",
                "submit_label": "Save changes",
                "event": form_values,
                "organizers": get_organizers(),
                "errors": errors,
            },
            status_code=400,
        )

    event_document["updatedAt"] = datetime.now(
        timezone.utc
    )

    result = database.events.update_one(
        {"_id": object_id},
        {"$set": event_document},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return redirect_with_message(
        "Event updated successfully."
    )


@router.post("/{event_id}/delete")
def delete_event(event_id: str):
    object_id = valid_object_id(event_id)

    result = database.events.delete_one(
        {"_id": object_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return redirect_with_message(
        "Event deleted successfully."
    )