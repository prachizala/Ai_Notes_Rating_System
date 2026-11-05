"""
NoteIQ Reference Data Seed Script
Seeds:
- Streams: BBA, BCA, B.Voc
- Semesters: 1 to 5 as 'active', 6 as 'coming_soon'
Rule: Idempotent - can be run multiple times safely without producing duplicates.
Subjects and topics are dynamic and are NOT seeded.
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy import select
from app.db.session import SyncSessionLocal
from app.db.models import Stream, Semester


STREAMS = [
    {"name": "Bachelor of Business Administration", "slug": "bba"},
    {"name": "Bachelor of Computer Applications", "slug": "bca"},
    {"name": "Bachelor of Vocation", "slug": "bvoc"},
]

SEMESTERS = [
    {"number": 1, "status": "active"},
    {"number": 2, "status": "active"},
    {"number": 3, "status": "active"},
    {"number": 4, "status": "active"},
    {"number": 5, "status": "active"},
    {"number": 6, "status": "coming_soon"},
]


def seed_reference_data():
    db = SyncSessionLocal()
    try:
        print("[INFO] Starting NoteIQ reference data seed...")

        # 1. Seed Streams
        for s in STREAMS:
            stmt = select(Stream).where(Stream.slug == s["slug"])
            existing = db.execute(stmt).scalar_one_or_none()
            if not existing:
                stream = Stream(name=s["name"], slug=s["slug"])
                db.add(stream)
                print(f"[CREATED] Stream: {s['name']} ({s['slug']})")
            else:
                existing.name = s["name"]
                print(f"[EXISTS] Stream: {s['slug']}")

        # 2. Seed Semesters
        for sem in SEMESTERS:
            stmt = select(Semester).where(Semester.number == sem["number"])
            existing = db.execute(stmt).scalar_one_or_none()
            if not existing:
                semester = Semester(number=sem["number"], status=sem["status"])
                db.add(semester)
                print(f"[CREATED] Semester {sem['number']} ({sem['status']})")
            else:
                existing.status = sem["status"]
                print(f"[EXISTS] Semester {sem['number']}")

        db.commit()
        print("[SUCCESS] Reference data seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed reference data: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_reference_data()
