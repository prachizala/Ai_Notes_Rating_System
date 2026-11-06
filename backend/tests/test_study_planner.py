import pytest
from app.services.study_planner import generate_study_plan
from app.schemas.study_planner import StudyPlannerResponse


def test_generate_study_plan_fallback():
    title = "Operating Systems Process Synchronization & Deadlocks"
    text = (
        "Process synchronization involves coordinating the execution of processes.\n"
        "Race conditions happen when multiple processes access shared data concurrently.\n"
        "Semaphores and mutex locks are fundamental synchronization primitives.\n"
        "Deadlock occurs when four conditions are met: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.\n"
        "Banker's Algorithm is used for deadlock avoidance in resource allocation.\n"
    )
    res = generate_study_plan(
        document_id="doc-plan-test",
        document_title=title,
        document_text=text,
        subject_name="Operating Systems",
    )
    assert isinstance(res, StudyPlannerResponse)
    assert res.document_id == "doc-plan-test"
    assert res.total_days == 7
    assert res.total_estimated_hours > 0
    assert len(res.days) == 7
    assert len(res.general_exam_tips) > 0

    for idx, day in enumerate(res.days):
        assert day.day_number == idx + 1
        assert len(day.theme) > 0
        assert day.estimated_minutes >= 30
        assert len(day.tasks) >= 2
        assert len(day.recall_challenge) > 10
        assert len(day.recommended_tool) > 0
