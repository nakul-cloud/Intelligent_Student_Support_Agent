"""Database seeder script.

Seeds 20 mock university student records, fee ledgers, scholarships, and support tickets
directly into the PostgreSQL Docker database using SQLAlchemy async sessions.
The runtime agent and API endpoints query these PostgreSQL tables directly.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively models mock dataset definition and idempotent PostgreSQL persistence.
- Open/Closed (OCP): New student cohorts or ticket categories can be added without modifying upsert engine logic.
- Dependency Inversion (DIP): Injects AsyncSessionLocal and SQLAlchemy engine.
"""

import asyncio
import bcrypt
from sqlalchemy import select
from app.config.database import AsyncSessionLocal, engine
from app.models.student_records import Student, FeeRecord, Scholarship, SupportTicket
from app.models.auth_credentials import AuthCredentials
from app.utils.logger import logger

# 20 Pre-enrolled university student profiles (Option 2)
MOCK_STUDENTS = [
    {
        "student_id": "STU001",
        "name": "Rahul Sharma",
        "programme": "PGDM AI and DS",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43210",
        "email": "rahul.sharma@university.edu",
        "address": "Hostel Block-B, Room 204",
        "fee": {
            "total_fee": 450000,
            "paid": 225000,
            "pending": 225000,
            "due_date": "2026-10-31",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0301",
        },
        "scholarship": {
            "scholarship_type": "Merit Scholarship",
            "percentage": 20,
            "amount_per_semester": 45000,
            "status": "Active",
        },
        "has_default_auth": True,
    },
    {
        "student_id": "STU002",
        "name": "Priya Patel",
        "programme": "MBA Marketing",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43211",
        "email": "priya.patel@university.edu",
        "address": "Hostel Block-A, Room 102",
        "fee": {
            "total_fee": 400000,
            "paid": 400000,
            "pending": 0,
            "due_date": "2026-08-15",
            "status": "Paid",
            "receipt": "RCP-2026-0810",
        },
        "scholarship": None,
        "has_default_auth": True,
    },
    {
        "student_id": "STU003",
        "name": "Amit Verma",
        "programme": "B.Tech CSE",
        "batch": "2024-28",
        "status": "Enrolled",
        "phone": "+91 98765 43212",
        "email": "amit.verma@university.edu",
        "address": "Day Scholar, Sector 62, Noida",
        "fee": {
            "total_fee": 350000,
            "paid": 150000,
            "pending": 200000,
            "due_date": "2026-09-01",
            "status": "Overdue",
            "receipt": "RCP-2026-0115",
        },
        "scholarship": {
            "scholarship_type": "Sports Scholarship",
            "percentage": 15,
            "amount_per_semester": 26250,
            "status": "Active",
        },
        "has_default_auth": True,
    },
    {
        "student_id": "STU004",
        "name": "Sneha Gupta",
        "programme": "M.Tech Data Science",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43213",
        "email": "sneha.gupta@university.edu",
        "address": "Hostel Block-C, Room 310",
        "fee": {
            "total_fee": 380000,
            "paid": 0,
            "pending": 380000,
            "due_date": "2026-11-15",
            "status": "Pending",
            "receipt": None,
        },
        "scholarship": {
            "scholarship_type": "Research Fellowship",
            "percentage": 25,
            "amount_per_semester": 47500,
            "status": "Active",
        },
        "has_default_auth": True,
    },
    {
        "student_id": "STU005",
        "name": "Vikram Singh",
        "programme": "BBA",
        "batch": "2025-28",
        "status": "Enrolled",
        "phone": "+91 98765 43214",
        "email": "vikram.singh@university.edu",
        "address": "Day Scholar, Indirapuram, Ghaziabad",
        "fee": {
            "total_fee": 300000,
            "paid": 300000,
            "pending": 0,
            "due_date": "2026-07-30",
            "status": "Paid",
            "receipt": "RCP-2026-0720",
        },
        "scholarship": None,
        "has_default_auth": True,
    },
    {
        "student_id": "STU006",
        "name": "Ananya Iyer",
        "programme": "B.Tech AI & ML",
        "batch": "2024-28",
        "status": "Enrolled",
        "phone": "+91 98765 43215",
        "email": "ananya.iyer@university.edu",
        "address": "Hostel Block-A, Room 215",
        "fee": {
            "total_fee": 420000,
            "paid": 210000,
            "pending": 210000,
            "due_date": "2026-11-30",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0412",
        },
        "scholarship": {
            "scholarship_type": "Women in Tech Award",
            "percentage": 30,
            "amount_per_semester": 63000,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU007",
        "name": "Rohan Mehta",
        "programme": "MBA Finance",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43216",
        "email": "rohan.mehta@university.edu",
        "address": "Hostel Block-B, Room 108",
        "fee": {
            "total_fee": 460000,
            "paid": 460000,
            "pending": 0,
            "due_date": "2026-08-30",
            "status": "Paid",
            "receipt": "RCP-2026-0822",
        },
        "scholarship": {
            "scholarship_type": "Dean's Honor Grant",
            "percentage": 10,
            "amount_per_semester": 23000,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU008",
        "name": "Pooja Nair",
        "programme": "MCA",
        "batch": "2024-26",
        "status": "Enrolled",
        "phone": "+91 98765 43217",
        "email": "pooja.nair@university.edu",
        "address": "Day Scholar, Mayur Vihar, Delhi",
        "fee": {
            "total_fee": 320000,
            "paid": 160000,
            "pending": 160000,
            "due_date": "2026-10-15",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0219",
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU009",
        "name": "Siddharth Rao",
        "programme": "B.Tech ECE",
        "batch": "2023-27",
        "status": "Enrolled",
        "phone": "+91 98765 43218",
        "email": "siddharth.rao@university.edu",
        "address": "Hostel Block-D, Room 402",
        "fee": {
            "total_fee": 360000,
            "paid": 120000,
            "pending": 240000,
            "due_date": "2026-09-15",
            "status": "Overdue",
            "receipt": "RCP-2026-0094",
        },
        "scholarship": {
            "scholarship_type": "State Talent Scholarship",
            "percentage": 20,
            "amount_per_semester": 36000,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU010",
        "name": "Tanvi Kulkarni",
        "programme": "PGDM Business Analytics",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43219",
        "email": "tanvi.k@university.edu",
        "address": "Hostel Block-C, Room 114",
        "fee": {
            "total_fee": 440000,
            "paid": 0,
            "pending": 440000,
            "due_date": "2026-11-20",
            "status": "Pending",
            "receipt": None,
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU011",
        "name": "Aditya Joshi",
        "programme": "B.Tech Mechanical",
        "batch": "2024-28",
        "status": "Enrolled",
        "phone": "+91 98765 43220",
        "email": "aditya.joshi@university.edu",
        "address": "Day Scholar, South Ex, New Delhi",
        "fee": {
            "total_fee": 340000,
            "paid": 340000,
            "pending": 0,
            "due_date": "2026-08-10",
            "status": "Paid",
            "receipt": "RCP-2026-0801",
        },
        "scholarship": {
            "scholarship_type": "Alumni Endowment",
            "percentage": 15,
            "amount_per_semester": 25500,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU012",
        "name": "Meera Nambiar",
        "programme": "MBA HR",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43221",
        "email": "meera.n@university.edu",
        "address": "Hostel Block-A, Room 305",
        "fee": {
            "total_fee": 390000,
            "paid": 195000,
            "pending": 195000,
            "due_date": "2026-10-25",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0318",
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU013",
        "name": "Karan Malhotra",
        "programme": "B.Tech IT",
        "batch": "2024-28",
        "status": "Enrolled",
        "phone": "+91 98765 43222",
        "email": "karan.m@university.edu",
        "address": "Hostel Block-B, Room 312",
        "fee": {
            "total_fee": 370000,
            "paid": 370000,
            "pending": 0,
            "due_date": "2026-07-25",
            "status": "Paid",
            "receipt": "RCP-2026-0715",
        },
        "scholarship": {
            "scholarship_type": "Merit Scholarship",
            "percentage": 25,
            "amount_per_semester": 46250,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU014",
        "name": "Riya Sengupta",
        "programme": "M.Tech Cyber Security",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43223",
        "email": "riya.s@university.edu",
        "address": "Day Scholar, Dwarka Sector 10, Delhi",
        "fee": {
            "total_fee": 395000,
            "paid": 100000,
            "pending": 295000,
            "due_date": "2026-09-20",
            "status": "Overdue",
            "receipt": "RCP-2026-0188",
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU015",
        "name": "Harshvardhan Jain",
        "programme": "B.Com (Hons)",
        "batch": "2025-28",
        "status": "Enrolled",
        "phone": "+91 98765 43224",
        "email": "harsh.jain@university.edu",
        "address": "Hostel Block-D, Room 101",
        "fee": {
            "total_fee": 280000,
            "paid": 280000,
            "pending": 0,
            "due_date": "2026-08-05",
            "status": "Paid",
            "receipt": "RCP-2026-0795",
        },
        "scholarship": {
            "scholarship_type": "Sports Fellowship",
            "percentage": 20,
            "amount_per_semester": 28000,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU016",
        "name": "Divya Deshmukh",
        "programme": "PGDM Fintech",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43225",
        "email": "divya.d@university.edu",
        "address": "Hostel Block-C, Room 208",
        "fee": {
            "total_fee": 470000,
            "paid": 235000,
            "pending": 235000,
            "due_date": "2026-11-05",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0490",
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU017",
        "name": "Manav Kapoor",
        "programme": "B.Tech Robotics",
        "batch": "2023-27",
        "status": "Enrolled",
        "phone": "+91 98765 43226",
        "email": "manav.k@university.edu",
        "address": "Hostel Block-B, Room 415",
        "fee": {
            "total_fee": 410000,
            "paid": 410000,
            "pending": 0,
            "due_date": "2026-08-18",
            "status": "Paid",
            "receipt": "RCP-2026-0815",
        },
        "scholarship": {
            "scholarship_type": "Innovation Fellowship",
            "percentage": 35,
            "amount_per_semester": 71750,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU018",
        "name": "Neha Chawla",
        "programme": "MBA Operations",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43227",
        "email": "neha.c@university.edu",
        "address": "Day Scholar, Greater Noida",
        "fee": {
            "total_fee": 385000,
            "paid": 0,
            "pending": 385000,
            "due_date": "2026-11-25",
            "status": "Pending",
            "receipt": None,
        },
        "scholarship": None,
        "has_default_auth": False,
    },
    {
        "student_id": "STU019",
        "name": "Arjun Pillai",
        "programme": "B.Tech Civil",
        "batch": "2024-28",
        "status": "Enrolled",
        "phone": "+91 98765 43228",
        "email": "arjun.p@university.edu",
        "address": "Hostel Block-D, Room 206",
        "fee": {
            "total_fee": 330000,
            "paid": 165000,
            "pending": 165000,
            "due_date": "2026-10-18",
            "status": "Partially Paid",
            "receipt": "RCP-2026-0345",
        },
        "scholarship": {
            "scholarship_type": "Merit Scholarship",
            "percentage": 15,
            "amount_per_semester": 24750,
            "status": "Active",
        },
        "has_default_auth": False,
    },
    {
        "student_id": "STU020",
        "name": "Shreya Banerjee",
        "programme": "M.Sc Data Analytics",
        "batch": "2025-27",
        "status": "Enrolled",
        "phone": "+91 98765 43229",
        "email": "shreya.b@university.edu",
        "address": "Hostel Block-A, Room 410",
        "fee": {
            "total_fee": 360000,
            "paid": 360000,
            "pending": 0,
            "due_date": "2026-07-28",
            "status": "Paid",
            "receipt": "RCP-2026-0730",
        },
        "scholarship": {
            "scholarship_type": "Chancellor's Gold Grant",
            "percentage": 50,
            "amount_per_semester": 90000,
            "status": "Active",
        },
        "has_default_auth": False,
    },
]

MOCK_TICKETS = [
    {
        "ticket_id": "TICK-90101",
        "student_id": "STU001",
        "category": "IT Facilities",
        "description": "Hostel Wi-Fi intermittent connectivity in Block-B second floor.",
        "priority": "Medium",
        "status": "Open",
    },
    {
        "ticket_id": "TICK-90102",
        "student_id": "STU001",
        "category": "Financial Services",
        "description": "Semester tuition receipt generation error on banking portal.",
        "priority": "Low",
        "status": "Resolved",
    },
    {
        "ticket_id": "TICK-90103",
        "student_id": "STU003",
        "category": "Financial Services",
        "description": "Tuition installment payment schedule extension request due to bank processing delay.",
        "priority": "High",
        "status": "In Review",
    },
    {
        "ticket_id": "TICK-90104",
        "student_id": "STU004",
        "category": "Academic Facilities",
        "description": "Data Science Research Lab 402 biometric sensor access permission.",
        "priority": "Medium",
        "status": "Resolved",
    },
    {
        "ticket_id": "TICK-90105",
        "student_id": "STU007",
        "category": "Hostel Administration",
        "description": "Mess rebate credit adjustment for university sports meet week.",
        "priority": "Low",
        "status": "Open",
    },
    {
        "ticket_id": "TICK-90106",
        "student_id": "STU009",
        "category": "Examination Branch",
        "description": "Request for official physical transcripts and provisional grade card verification.",
        "priority": "Medium",
        "status": "In Review",
    },
]


async def seed_database() -> None:
    """Populate PostgreSQL database with mock student, fee, scholarship, and ticket records."""
    logger.info("Starting PostgreSQL database seeding for Option 2...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Upsert Student Profiles
            for item in MOCK_STUDENTS:
                student_id = item["student_id"]

                res = await session.execute(
                    select(Student).where(Student.student_id == student_id)
                )
                student = res.scalar_one_or_none()

                if not student:
                    student = Student(
                        student_id=student_id,
                        name=item["name"],
                        programme=item["programme"],
                        batch=item["batch"],
                        status=item["status"],
                        phone=item.get("phone"),
                        email=item.get("email"),
                        address=item.get("address"),
                    )
                    session.add(student)
                    await session.flush()
                    logger.info(f"  [+] Enrolled student profile: {student_id} - {item['name']}")
                else:
                    student.name = item["name"]
                    student.programme = item["programme"]
                    student.batch = item["batch"]
                    student.status = item["status"]
                    student.phone = item.get("phone")
                    student.email = item.get("email")
                    student.address = item.get("address")
                    logger.info(f"  [*] Synchronized student profile: {student_id}")

                # 2. Upsert Fee Record
                fee_info = item["fee"]
                fee_res = await session.execute(
                    select(FeeRecord).where(FeeRecord.student_id == student_id)
                )
                fee_record = fee_res.scalar_one_or_none()

                if not fee_record:
                    fee_record = FeeRecord(
                        student_id=student_id,
                        total_fee=fee_info["total_fee"],
                        paid=fee_info["paid"],
                        pending=fee_info["pending"],
                        due_date=fee_info["due_date"],
                        status=fee_info["status"],
                        receipt=fee_info["receipt"],
                    )
                    session.add(fee_record)
                    logger.info(f"  [+] Created fee record for {student_id}: {fee_info['status']}")
                else:
                    fee_record.total_fee = fee_info["total_fee"]
                    fee_record.paid = fee_info["paid"]
                    fee_record.pending = fee_info["pending"]
                    fee_record.due_date = fee_info["due_date"]
                    fee_record.status = fee_info["status"]
                    fee_record.receipt = fee_info["receipt"]
                    logger.info(f"  [*] Updated fee record for {student_id}")

                # 3. Upsert Scholarship Record
                scholarship_info = item["scholarship"]
                schol_res = await session.execute(
                    select(Scholarship).where(Scholarship.student_id == student_id)
                )
                schol_record = schol_res.scalar_one_or_none()

                if scholarship_info:
                    if not schol_record:
                        schol_record = Scholarship(
                            student_id=student_id,
                            scholarship_type=scholarship_info["scholarship_type"],
                            percentage=scholarship_info["percentage"],
                            amount_per_semester=scholarship_info["amount_per_semester"],
                            status=scholarship_info["status"],
                        )
                        session.add(schol_record)
                        logger.info(f"  [+] Created scholarship for {student_id}: {scholarship_info['scholarship_type']}")
                    else:
                        schol_record.scholarship_type = scholarship_info["scholarship_type"]
                        schol_record.percentage = scholarship_info["percentage"]
                        schol_record.amount_per_semester = scholarship_info["amount_per_semester"]
                        schol_record.status = scholarship_info["status"]
                        logger.info(f"  [*] Updated scholarship for {student_id}")
                else:
                    if schol_record:
                        await session.delete(schol_record)
                        logger.info(f"  [-] Removed scholarship for {student_id}")

                # 4. Default Auth Credentials for active starter accounts (STU001 - STU005)
                # STU006 through STU020 are available to be claimed / registered by user on /signup
                if item.get("has_default_auth", False):
                    auth_res = await session.execute(
                        select(AuthCredentials).where(AuthCredentials.student_id == student_id)
                    )
                    auth_record = auth_res.scalar_one_or_none()

                    if not auth_record:
                        default_pw = "Student@123"
                        hashed_pw = bcrypt.hashpw(default_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                        auth_record = AuthCredentials(
                            student_id=student_id,
                            hashed_password=hashed_pw,
                        )
                        session.add(auth_record)
                        logger.info(f"  [+] Created default auth credentials for {student_id} (Student@123)")

            # 5. Upsert Support Tickets
            for t_item in MOCK_TICKETS:
                ticket_res = await session.execute(
                    select(SupportTicket).where(SupportTicket.ticket_id == t_item["ticket_id"])
                )
                ticket_record = ticket_res.scalar_one_or_none()
                if not ticket_record:
                    ticket_record = SupportTicket(
                        ticket_id=t_item["ticket_id"],
                        student_id=t_item["student_id"],
                        category=t_item["category"],
                        description=t_item["description"],
                        priority=t_item["priority"],
                        status=t_item["status"],
                    )
                    session.add(ticket_record)
                    logger.info(f"  [+] Created ticket {t_item['ticket_id']} for {t_item['student_id']}")
                else:
                    ticket_record.category = t_item["category"]
                    ticket_record.description = t_item["description"]
                    ticket_record.priority = t_item["priority"]
                    ticket_record.status = t_item["status"]
                    logger.info(f"  [*] Updated ticket {t_item['ticket_id']}")

            await session.commit()
            logger.info("Database seeding successfully committed to PostgreSQL for all 20 enrolled students!")

        except Exception as exc:
            await session.rollback()
            logger.error(f"PostgreSQL seeding failed: {exc}")
            raise
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
