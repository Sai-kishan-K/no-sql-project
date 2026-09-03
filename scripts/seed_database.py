from datetime import datetime, timedelta, timezone

from pymongo.errors import PyMongoError

from app.database import database


NOW = datetime.now(timezone.utc)


USERS = [
    {
        "firstName": "Emma",
        "lastName": "Martin",
        "email": "emma.martin@campus.fr",
        "department": "Computer Science",
        "role": "student",
        "interests": ["MongoDB", "Python", "Artificial Intelligence"],
        "createdAt": NOW,
    },
    {
        "firstName": "Lucas",
        "lastName": "Bernard",
        "email": "lucas.bernard@campus.fr",
        "department": "Data Engineering",
        "role": "student",
        "interests": ["Data Engineering", "Cloud", "MongoDB"],
        "createdAt": NOW,
    },
    {
        "firstName": "Sophie",
        "lastName": "Dubois",
        "email": "sophie.dubois@campus.fr",
        "department": "Business",
        "role": "organizer",
        "interests": ["Entrepreneurship", "Marketing", "Networking"],
        "createdAt": NOW,
    },
    {
        "firstName": "Hugo",
        "lastName": "Robert",
        "email": "hugo.robert@campus.fr",
        "department": "Cybersecurity",
        "role": "student",
        "interests": ["Cybersecurity", "Cloud", "Programming"],
        "createdAt": NOW,
    },
    {
        "firstName": "Chloe",
        "lastName": "Richard",
        "email": "chloe.richard@campus.fr",
        "department": "Design",
        "role": "student",
        "interests": ["Design", "Photography", "Web Development"],
        "createdAt": NOW,
    },
    {
        "firstName": "Louis",
        "lastName": "Petit",
        "email": "louis.petit@campus.fr",
        "department": "Computer Science",
        "role": "student",
        "interests": ["Python", "Web Development", "Gaming"],
        "createdAt": NOW,
    },
    {
        "firstName": "Lea",
        "lastName": "Durand",
        "email": "lea.durand@campus.fr",
        "department": "Artificial Intelligence",
        "role": "student",
        "interests": ["Artificial Intelligence", "Robotics", "Python"],
        "createdAt": NOW,
    },
    {
        "firstName": "Nathan",
        "lastName": "Leroy",
        "email": "nathan.leroy@campus.fr",
        "department": "Business",
        "role": "student",
        "interests": ["Finance", "Entrepreneurship", "Sports"],
        "createdAt": NOW,
    },
    {
        "firstName": "Camille",
        "lastName": "Moreau",
        "email": "camille.moreau@campus.fr",
        "department": "Data Engineering",
        "role": "student",
        "interests": ["MongoDB", "Analytics", "Cloud"],
        "createdAt": NOW,
    },
    {
        "firstName": "Thomas",
        "lastName": "Simon",
        "email": "thomas.simon@campus.fr",
        "department": "Sports",
        "role": "student",
        "interests": ["Football", "Fitness", "Health"],
        "createdAt": NOW,
    },
    {
        "firstName": "Manon",
        "lastName": "Laurent",
        "email": "manon.laurent@campus.fr",
        "department": "Marketing",
        "role": "student",
        "interests": ["Marketing", "Social Media", "Photography"],
        "createdAt": NOW,
    },
    {
        "firstName": "Gabriel",
        "lastName": "Michel",
        "email": "gabriel.michel@campus.fr",
        "department": "Computer Science",
        "role": "staff",
        "interests": ["Programming", "MongoDB", "Teaching"],
        "createdAt": NOW,
    },
    {
        "firstName": "Sarah",
        "lastName": "Garcia",
        "email": "sarah.garcia@campus.fr",
        "department": "Student Services",
        "role": "organizer",
        "interests": ["Community", "Culture", "Education"],
        "createdAt": NOW,
    },
    {
        "firstName": "Arthur",
        "lastName": "David",
        "email": "arthur.david@campus.fr",
        "department": "Artificial Intelligence",
        "role": "staff",
        "interests": ["Artificial Intelligence", "Research", "Robotics"],
        "createdAt": NOW,
    },
    {
        "firstName": "Ines",
        "lastName": "Bertrand",
        "email": "ines.bertrand@campus.fr",
        "department": "International Relations",
        "role": "organizer",
        "interests": ["Culture", "Languages", "Travel"],
        "createdAt": NOW,
    },
]


EVENT_SPECS = [
    (
        "MongoDB Fundamentals Workshop",
        "Learn document modelling, queries, and indexes with MongoDB.",
        "Workshop",
        ["MongoDB", "NoSQL", "Database"],
        3,
        -35,
        35,
        "Technology Building",
        "T201",
        0,
        5,
    ),
    (
        "Python for Data Analysis",
        "Practical data analysis using Python and Pandas.",
        "Workshop",
        ["Python", "Data", "Analytics"],
        11,
        -28,
        40,
        "Technology Building",
        "T105",
        0,
        4,
    ),
    (
        "Campus Football Tournament",
        "A friendly football competition between departments.",
        "Sports",
        ["Football", "Fitness", "Competition"],
        12,
        -20,
        60,
        "Campus Stadium",
        "Field A",
        2,
        5,
    ),
    (
        "AI Research Seminar",
        "Presentations about recent developments in artificial intelligence.",
        "Seminar",
        ["AI", "Research", "Machine Learning"],
        13,
        -14,
        50,
        "Research Centre",
        "R301",
        1,
        4,
    ),
    (
        "International Culture Evening",
        "Students share food, music, and traditions from their countries.",
        "Cultural",
        ["Culture", "Languages", "Community"],
        14,
        -7,
        80,
        "Student Centre",
        "Main Hall",
        2,
        5,
    ),
    (
        "Introduction to Cloud Computing",
        "An introductory session covering modern cloud platforms.",
        "Seminar",
        ["Cloud", "Technology", "Data"],
        11,
        3,
        45,
        "Technology Building",
        "T202",
        0,
        4,
    ),
    (
        "Startup Networking Night",
        "Meet student founders, professionals, and potential collaborators.",
        "Networking",
        ["Startup", "Business", "Networking"],
        2,
        6,
        70,
        "Business Building",
        "B101",
        1,
        4,
    ),
    (
        "Cybersecurity Awareness Session",
        "Learn about phishing, passwords, and online safety.",
        "Seminar",
        ["Cybersecurity", "Security", "Technology"],
        11,
        9,
        55,
        "Technology Building",
        "T301",
        3,
        4,
    ),
    (
        "Photography Walk",
        "Explore the campus and practise urban photography techniques.",
        "Cultural",
        ["Photography", "Design", "Community"],
        14,
        12,
        25,
        "Student Centre",
        "Entrance",
        4,
        3,
    ),
    (
        "Data Engineering Bootcamp",
        "Build a practical data pipeline from ingestion to analysis.",
        "Workshop",
        ["Data Engineering", "MongoDB", "Python"],
        11,
        15,
        30,
        "Data Laboratory",
        "D204",
        5,
        5,
    ),
    (
        "Career Preparation Day",
        "CV reviews, interview practice, and career guidance.",
        "Career",
        ["Career", "Interview", "Networking"],
        12,
        18,
        90,
        "Student Centre",
        "Main Hall",
        6,
        4,
    ),
    (
        "Robotics Demonstration",
        "Students demonstrate their latest robotics projects.",
        "Technology",
        ["Robotics", "AI", "Innovation"],
        13,
        21,
        65,
        "Innovation Laboratory",
        "I101",
        7,
        4,
    ),
    (
        "Digital Marketing Masterclass",
        "Learn practical digital marketing and social-media strategies.",
        "Workshop",
        ["Marketing", "Social Media", "Business"],
        2,
        25,
        45,
        "Business Building",
        "B202",
        8,
        4,
    ),
    (
        "Campus Fitness Challenge",
        "A guided fitness challenge suitable for all students.",
        "Sports",
        ["Fitness", "Health", "Community"],
        12,
        29,
        50,
        "Campus Gym",
        "Training Hall",
        9,
        3,
    ),
    (
        "Web Development Hackathon",
        "Teams build a web application during a one-day hackathon.",
        "Competition",
        ["Programming", "Web Development", "Innovation"],
        11,
        33,
        40,
        "Technology Building",
        "T401",
        10,
        4,
    ),
    (
        "Finance for Entrepreneurs",
        "Understand budgeting, funding, and financial planning.",
        "Seminar",
        ["Finance", "Startup", "Business"],
        2,
        38,
        55,
        "Business Building",
        "B204",
        11,
        3,
    ),
    (
        "Student Art Exhibition",
        "An exhibition featuring artwork created by campus students.",
        "Cultural",
        ["Art", "Design", "Community"],
        14,
        45,
        100,
        "Campus Gallery",
        "Gallery 1",
        12,
        0,
    ),
    (
        "End-of-Term Community Meetup",
        "An informal meetup for students and staff across departments.",
        "Networking",
        ["Community", "Networking", "Culture"],
        12,
        52,
        120,
        "Student Centre",
        "Main Hall",
        13,
        0,
    ),
]


def build_registration(user_ids, user_index):
    return {
        "userId": user_ids[user_index],
        "registeredAt": NOW - timedelta(days=2),
        "status": "confirmed",
    }


def build_events(user_ids):
    events = []

    for index, spec in enumerate(EVENT_SPECS):
        (
            title,
            description,
            category,
            tags,
            organizer_index,
            day_offset,
            capacity,
            building,
            room,
            registration_start,
            registration_count,
        ) = spec

        start_date = NOW + timedelta(days=day_offset)
        end_date = start_date + timedelta(hours=2)

        registrations = []

        for position in range(registration_count):
            user_index = (registration_start + position) % len(user_ids)

            if user_index == organizer_index:
                user_index = (user_index + 1) % len(user_ids)

            registrations.append(
                build_registration(user_ids, user_index)
            )

        events.append(
            {
                "title": title,
                "description": description,
                "category": category,
                "tags": tags,
                "startDate": start_date,
                "endDate": end_date,
                "capacity": capacity,
                "location": {
                    "building": building,
                    "room": room,
                    "address": "Aivancity Campus, Villejuif, France",
                },
                "organizerId": user_ids[organizer_index],
                "registrations": registrations,
                "createdAt": NOW,
                "updatedAt": NOW,
            }
        )

    return events


def seed_database():
    try:
        database.client.admin.command("ping")
        print("Connected to MongoDB.")

        # Reset only the two project collections.
        database.events.delete_many({})
        database.users.delete_many({})

        user_result = database.users.insert_many(USERS)
        user_ids = user_result.inserted_ids

        events = build_events(user_ids)
        event_result = database.events.insert_many(events)

        registration_count = sum(
            len(event["registrations"]) for event in events
        )

        print(f"Inserted {len(user_ids)} users.")
        print(f"Inserted {len(event_result.inserted_ids)} events.")
        print(f"Inserted {registration_count} embedded registrations.")
        print("Database seeded successfully.")

    except PyMongoError as error:
        print(f"Database seeding failed: {error}")
        raise

#sadsad 
if __name__ == "__main__":
    seed_database()