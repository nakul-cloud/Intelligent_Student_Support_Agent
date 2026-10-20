"""Database seeder script.

Seeds mock university student records, fee ledgers, and scholarships
directly into the PostgreSQL Docker database using SQLAlchemy async sessions.
The runtime agent and tools query these PostgreSQL tables directly.
"""

import asyncio
from sqlalchemy import select, delete
from app.config.database import AsyncSessionLocal, engine
from app.models.student_records import Student, FeeRecord, Scholarship
from app.utils.logger import logger

# Initial mock data to be seeded directly into PostgreSQL
MOCK_STUDENTS = [
    {
        "student_id": "STU001",
        "name": "Rahul Sharma",
        "programme": "PGDM AI and DS",
        "batch": "2025-27",
        "status": "Enrolled",
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
    },
    {
        "student_id": "STU002",
        "name": "Priya Patel",
        "programme": "MBA Marketing",
        "batch": "2025-27",
        "status": "Enrolled",
        "fee": {
            "total_fee": 400000,
            "paid": 400000,
            "pending": 0,
            "due_date": "2026-08-15",
            "status": "Paid",
            "receipt": "RCP-2026-0810",
        },
        "scholarship": None,
    },
    {
        "student_id": "STU003",
        "name": "Amit Verma",
        "programme": "B.Tech CSE",
        "batch": "2024-28",
        "status": "Enrolled",
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
    },
    {
        "student_id": "STU004",
        "name": "Sneha Gupta",
        "programme": "M.Tech Data Science",
        "batch": "2025-27",
        "status": "Enrolled",
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
    },
    {
        "student_id": "STU005",
        "name": "Vikram Singh",
        "programme": "BBA",
        "batch": "2025-28",
        "status": "Enrolled",
        "fee": {
            "total_fee": 300000,
            "paid": 300000,
            "pending": 0,
            "due_date": "2026-07-30",
            "status": "Paid",
            "receipt": "RCP-2026-0720",
        },
        "scholarship": None,
    },
]


async def seed_database() -> None:
    """Populate PostgreSQL database with mock student, fee, and scholarship records."""
    logger.info("Starting PostgreSQL database seeding...")

    async with AsyncSessionLocal() as session:
        try:
            for item in MOCK_STUDENTS:
                student_id = item["student_id"]

                # 1. Upsert Student Record
                result = await session.execute(
                    select(Student).where(Student.student_id == student_id)
                )
                student = result.scalar_one_or_none()

                if not student:
                    student = Student(
                        student_id=student_id,
                        name=item["name"],
                        programme=item["programme"],
                        batch=item["batch"],
                        status=item["status"],
                    )
                    session.add(student)
                    await session.flush()
                    logger.info(f"  [+] Created student profile: {student_id} - {item['name']}")
                else:
                    student.name = item["name"]
                    student.programme = item["programme"]
                    student.batch = item["batch"]
                    student.status = item["status"]
                    logger.info(f"  [*] Updated student profile: {student_id}")

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

                # 3. Upsert Scholarship Record (if eligible)
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

            await session.commit()
            logger.info("Database seeding successfully committed to PostgreSQL!")

        except Exception as exc:
            await session.rollback()
            logger.error(f"Seeding failed: {exc}")
            raise
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
