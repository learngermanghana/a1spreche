from src.services.proficiency_profile import (
    PROFICIENCY_TAGS,
    REMEDIATION_TAGS,
    ProfileStore,
    build_planner_prompt,
)


def test_tags_are_defined_for_all_dimensions():
    expected = {"cohesion", "register", "accuracy", "range", "fluency"}
    assert set(PROFICIENCY_TAGS) == expected
    assert set(REMEDIATION_TAGS) == expected


def test_record_task_completion_filters_and_counts_errors():
    store = ProfileStore(history_limit=5)
    store.record_task_completion(
        student_code="stu-1",
        task_id="task-1",
        score=72.5,
        errors=["cohesion", "unknown", "accuracy"],
    )
    store.record_task_completion(
        student_code="stu-1",
        task_id="task-2",
        errors=["accuracy", "register"],
    )

    snapshot = store.snapshot("stu-1")
    assert snapshot["error_counts"]["accuracy"] == 2
    assert snapshot["error_counts"]["cohesion"] == 1
    assert snapshot["error_counts"]["register"] == 1
    history = snapshot["history"]
    assert len(history) == 2
    assert history[-1].task_id == "task-2"
    assert history[0].errors == ["cohesion", "accuracy"]


def test_planner_prompt_surfaces_gaps_and_recent_tasks():
    store = ProfileStore(history_limit=3)
    store.record_task_completion(
        student_code="stu-99",
        task_id="draft-1",
        score=50,
        errors=["cohesion", "cohesion", "range"],
    )
    store.record_task_completion(
        student_code="stu-99",
        task_id="draft-2",
        score=82,
        errors=["register"],
    )

    prompt = build_planner_prompt(
        student_code="stu-99",
        available_tasks=[
            {"id": "revise-cohesion", "focus_tags": ["cohesion", "accuracy"], "label": "Cohesion Drills"},
            {"id": "fluency-loop", "focus_tags": ["fluency"], "label": "Fluency Loop"},
        ],
        profile_store=store,
    )

    assert "Cohesion Drills" in prompt
    assert "revise-cohesion" in prompt
    assert "Cohesion" in prompt  # remediation line capitalised
    assert "recent flags" in prompt
    assert "draft-2" in prompt
    assert "fluency" in prompt  # from available task focus
