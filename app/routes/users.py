import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from bson import ObjectId
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.database import database


router = APIRouter(prefix="/users", tags=["Users"])

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

VALID_ROLES = [
    "student",
    "staff",
    "organizer",
]


def valid_user_object_id(user_id: str) -> ObjectId:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=404,
            detail="Invalid user identifier",
        )

    return ObjectId(user_id)


def redirect_to_users(
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
        url=f"/users?{parameters}",
        status_code=303,
    )


def redirect_to_user(
    user_id: str,
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
        url=f"/users/{user_id}?{parameters}",
        status_code=303,
    )


def prepare_user_form(user=None) -> dict:
    if not user:
        return {
            "firstName": "",
            "lastName": "",
            "email": "",
            "department": "",
            "role": "",
            "interestsText": "",
        }

    prepared_user = user.copy()

    prepared_user["interestsText"] = ", ".join(
        user.get("interests", [])
    )

    return prepared_user


def validate_user_form(
    first_name: str,
    last_name: str,
    email: str,
    department: str,
    role: str,
    interests: str,
):
    errors = []

    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()
    department = department.strip()

    interest_list = [
        interest.strip()
        for interest in interests.split(",")
        if interest.strip()
    ]

    if not first_name:
        errors.append("First name is required.")

    if not last_name:
        errors.append("Last name is required.")

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, email):
        errors.append("Enter a valid email address.")

    if not department:
        errors.append("Department is required.")

    if role not in VALID_ROLES:
        errors.append("Select a valid role.")

    if not interest_list:
        errors.append("Add at least one interest.")

    user_document = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "department": department,
        "role": role,
        "interests": interest_list,
    }

    return errors, user_document


@router.get("", response_class=HTMLResponse)
def list_users(
    request: Request,
    q: str = "",
    department: str = "",
    role: str = "",
    message: str = "",
    message_type: str = "success",
):
    match_conditions = []

    if q.strip():
        safe_search = re.escape(q.strip())

        match_conditions.append(
            {
                "$or": [
                    {
                        "firstName": {
                            "$regex": safe_search,
                            "$options": "i",
                        }
                    },
                    {
                        "lastName": {
                            "$regex": safe_search,
                            "$options": "i",
                        }
                    },
                    {
                        "email": {
                            "$regex": safe_search,
                            "$options": "i",
                        }
                    },
                ]
            }
        )

    if department:
        match_conditions.append(
            {"department": department}
        )

    if role:
        match_conditions.append({"role": role})

    pipeline = []

    if match_conditions:
        pipeline.append(
            {
                "$match": {
                    "$and": match_conditions,
                }
            }
        )

    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "events",
                    "localField": "_id",
                    "foreignField": "registrations.userId",
                    "as": "registeredEvents",
                }
            },
            {
                "$addFields": {
                    "registrationCount": {
                        "$size": "$registeredEvents"
                    }
                }
            },
            {
                "$project": {
                    "firstName": 1,
                    "lastName": 1,
                    "email": 1,
                    "department": 1,
                    "role": 1,
                    "interests": 1,
                    "createdAt": 1,
                    "registrationCount": 1,
                }
            },
            {
                "$sort": {
                    "lastName": 1,
                    "firstName": 1,
                }
            },
        ]
    )

    users = list(
        database.users.aggregate(pipeline)
    )

    departments = sorted(
        database.users.distinct("department")
    )

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "page_title": "Users",
            "active_page": "users",
            "users": users,
            "departments": departments,
            "roles": VALID_ROLES,
            "filters": {
                "q": q,
                "department": department,
                "role": role,
            },
            "message": message,
            "message_type": message_type,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def create_user_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="user_form.html",
        context={
            "page_title": "Create User",
            "active_page": "users",
            "form_heading": "Create User",
            "form_action": "/users/new",
            "submit_label": "Create user",
            "user": prepare_user_form(),
            "roles": VALID_ROLES,
            "errors": [],
        },
    )


@router.post("/new")
def create_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    role: str = Form(...),
    interests: str = Form(...),
):
    errors, user_document = validate_user_form(
        first_name,
        last_name,
        email,
        department,
        role,
        interests,
    )

    form_values = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "department": department,
        "role": role,
        "interestsText": interests,
    }

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="user_form.html",
            context={
                "page_title": "Create User",
                "active_page": "users",
                "form_heading": "Create User",
                "form_action": "/users/new",
                "submit_label": "Create user",
                "user": form_values,
                "roles": VALID_ROLES,
                "errors": errors,
            },
            status_code=400,
        )

    user_document["createdAt"] = datetime.now(
        timezone.utc
    )

    try:
        database.users.insert_one(user_document)
    except DuplicateKeyError:
        return templates.TemplateResponse(
            request=request,
            name="user_form.html",
            context={
                "page_title": "Create User",
                "active_page": "users",
                "form_heading": "Create User",
                "form_action": "/users/new",
                "submit_label": "Create user",
                "user": form_values,
                "roles": VALID_ROLES,
                "errors": [
                    "A user with this email already exists."
                ],
            },
            status_code=400,
        )

    return redirect_to_users(
        "User created successfully."
    )


@router.get("/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    request: Request,
    user_id: str,
):
    object_id = valid_user_object_id(user_id)

    user = database.users.find_one(
        {"_id": object_id}
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="user_form.html",
        context={
            "page_title": "Edit User",
            "active_page": "users",
            "form_heading": "Edit User",
            "form_action": f"/users/{user_id}/edit",
            "submit_label": "Save changes",
            "user": prepare_user_form(user),
            "roles": VALID_ROLES,
            "errors": [],
        },
    )


@router.post("/{user_id}/edit")
def update_user(
    request: Request,
    user_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    role: str = Form(...),
    interests: str = Form(...),
):
    object_id = valid_user_object_id(user_id)

    existing_user = database.users.find_one(
        {"_id": object_id}
    )

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    errors, user_document = validate_user_form(
        first_name,
        last_name,
        email,
        department,
        role,
        interests,
    )

    form_values = {
        "_id": object_id,
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "department": department,
        "role": role,
        "interestsText": interests,
    }

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="user_form.html",
            context={
                "page_title": "Edit User",
                "active_page": "users",
                "form_heading": "Edit User",
                "form_action": f"/users/{user_id}/edit",
                "submit_label": "Save changes",
                "user": form_values,
                "roles": VALID_ROLES,
                "errors": errors,
            },
            status_code=400,
        )

    try:
        database.users.update_one(
            {"_id": object_id},
            {
                "$set": user_document,
            },
        )
    except DuplicateKeyError:
        return templates.TemplateResponse(
            request=request,
            name="user_form.html",
            context={
                "page_title": "Edit User",
                "active_page": "users",
                "form_heading": "Edit User",
                "form_action": f"/users/{user_id}/edit",
                "submit_label": "Save changes",
                "user": form_values,
                "roles": VALID_ROLES,
                "errors": [
                    "A user with this email already exists."
                ],
            },
            status_code=400,
        )

    return redirect_to_user(
        user_id,
        "User updated successfully.",
    )


@router.post("/{user_id}/delete")
def delete_user(user_id: str):
    object_id = valid_user_object_id(user_id)

    user = database.users.find_one(
        {"_id": object_id},
        {
            "firstName": 1,
            "lastName": 1,
        },
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    references = database.events.count_documents(
        {
            "$or": [
                {"organizerId": object_id},
                {"registrations.userId": object_id},
            ]
        }
    )

    if references > 0:
        return redirect_to_user(
            user_id,
            (
                "This user cannot be deleted because they are "
                "an organizer or registered for an event."
            ),
            "danger",
        )

    database.users.delete_one(
        {"_id": object_id}
    )

    return redirect_to_users(
        (
            f"{user['firstName']} {user['lastName']} "
            "was deleted successfully."
        )
    )


@router.get("/{user_id}", response_class=HTMLResponse)
def user_details(
    request: Request,
    user_id: str,
    message: str = "",
    message_type: str = "success",
):
    object_id = valid_user_object_id(user_id)

    user = database.users.find_one(
        {"_id": object_id}
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    participation_pipeline = [
        {
            "$match": {
                "registrations.userId": object_id,
            }
        },
        {
            "$unwind": "$registrations"
        },
        {
            "$match": {
                "registrations.userId": object_id,
            }
        },
        {
            "$project": {
                "title": 1,
                "category": 1,
                "startDate": 1,
                "endDate": 1,
                "location": 1,
                "registrationStatus": (
                    "$registrations.status"
                ),
                "registeredAt": (
                    "$registrations.registeredAt"
                ),
            }
        },
        {
            "$sort": {
                "startDate": 1,
            }
        },
    ]

    registrations = list(
        database.events.aggregate(
            participation_pipeline
        )
    )

    now = datetime.now(timezone.utc)

    for registration in registrations:
        registration["isUpcoming"] = (
            registration["startDate"] >= now
        )

    upcoming_count = sum(
        1
        for registration in registrations
        if registration["isUpcoming"]
    )

    past_count = (
        len(registrations) - upcoming_count
    )

    return templates.TemplateResponse(
        request=request,
        name="user_detail.html",
        context={
            "page_title": (
                f"{user['firstName']} "
                f"{user['lastName']}"
            ),
            "active_page": "users",
            "user": user,
            "registrations": registrations,
            "upcoming_count": upcoming_count,
            "past_count": past_count,
            "message": message,
            "message_type": message_type,
        },
    )
