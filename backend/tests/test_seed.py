import sys
import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.constants import STREAMS, SEMESTERS
from app.db.base import Base
from app.db.models import Stream, Semester


def test_seed_idempotency():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Function simulating seed logic on the session
    def run_seed():
        for s in STREAMS:
            stmt = select(Stream).where(Stream.slug == s["slug"])
            existing = session.execute(stmt).scalar_one_or_none()
            if not existing:
                stream = Stream(name=s["name"], slug=s["slug"])
                session.add(stream)
            else:
                existing.name = s["name"]

        for sem in SEMESTERS:
            stmt = select(Semester).where(Semester.number == sem["number"])
            existing = session.execute(stmt).scalar_one_or_none()
            if not existing:
                semester = Semester(number=sem["number"], status=sem["status"])
                session.add(semester)
            else:
                existing.status = sem["status"]
        session.commit()

    # Run 1st time
    run_seed()
    streams_count_1 = session.query(Stream).count()
    semesters_count_1 = session.query(Semester).count()

    assert streams_count_1 == 3
    assert semesters_count_1 == 6

    # Verify Semester 6 status is coming_soon, 1 to 5 are active
    sem6 = session.execute(select(Semester).where(Semester.number == 6)).scalar_one()
    assert sem6.status == "coming_soon"
    for num in range(1, 6):
        sem = session.execute(select(Semester).where(Semester.number == num)).scalar_one()
        assert sem.status == "active"

    # Run 2nd time (idempotency check)
    run_seed()
    streams_count_2 = session.query(Stream).count()
    semesters_count_2 = session.query(Semester).count()

    assert streams_count_2 == streams_count_1
    assert semesters_count_2 == semesters_count_1

    session.close()
