"""Courses and assignments API endpoints."""

from datetime import datetime, time, date
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import CourseTable, AssignmentTable
from app.models.academic import Course, Assignment, CourseCreate, AssignmentCreate
from app.models.base import Priority, TimeSlotPreference

router = APIRouter()


# Course endpoints
@router.get("/", response_model=list[Course])
async def list_courses(db: Session = Depends(get_db)):
    """List all courses."""
    courses = db.query(CourseTable).order_by(CourseTable.code).all()
    return [_course_to_model(c) for c in courses]


@router.get("/{course_id}", response_model=Course)
async def get_course(course_id: str, db: Session = Depends(get_db)):
    """Get a specific course by ID."""
    course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return _course_to_model(course)


@router.post("/", response_model=Course, status_code=201)
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    db_course = CourseTable(
        id=str(uuid4()),
        code=course.code,
        name=course.name,
        day_of_week=course.day_of_week,
        start_time=course.start_time.strftime("%H:%M"),
        end_time=course.end_time.strftime("%H:%M"),
        location=course.location,
        semester_start=datetime.combine(course.semester_start, time.min),
        semester_end=datetime.combine(course.semester_end, time.min),
        excluded_dates=[d.isoformat() for d in course.excluded_dates],
        source_adapter="manual",
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return _course_to_model(db_course)


@router.delete("/{course_id}", status_code=204)
async def delete_course(course_id: str, db: Session = Depends(get_db)):
    """Delete a course and its assignments."""
    course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Delete associated assignments
    db.query(AssignmentTable).filter(AssignmentTable.course_id == course_id).delete()
    db.delete(course)
    db.commit()


# Assignment endpoints
@router.get("/{course_id}/assignments", response_model=list[Assignment])
async def list_assignments(
    course_id: str,
    include_completed: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List assignments for a course."""
    query = db.query(AssignmentTable).filter(AssignmentTable.course_id == course_id)
    if not include_completed:
        query = query.filter(AssignmentTable.is_completed == False)
    assignments = query.order_by(AssignmentTable.due_date).all()
    return [_assignment_to_model(a) for a in assignments]


@router.get("/assignments/upcoming", response_model=list[Assignment])
async def list_upcoming_assignments(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """List upcoming assignments across all courses."""
    cutoff = datetime.utcnow() + timedelta(days=days)
    assignments = (
        db.query(AssignmentTable)
        .filter(AssignmentTable.is_completed == False)
        .filter(AssignmentTable.due_date <= cutoff)
        .order_by(AssignmentTable.due_date)
        .all()
    )
    return [_assignment_to_model(a) for a in assignments]


@router.post("/{course_id}/assignments", response_model=Assignment, status_code=201)
async def create_assignment(
    course_id: str, assignment: AssignmentCreate, db: Session = Depends(get_db)
):
    """Create a new assignment for a course."""
    # Verify course exists
    course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_assignment = AssignmentTable(
        id=str(uuid4()),
        course_id=course_id,
        name=assignment.name,
        description=assignment.description,
        due_date=assignment.due_date,
        estimated_hours=assignment.estimated_hours,
        priority=assignment.priority.value,
        preferred_time_slots=[TimeSlotPreference.ANY.value],
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return _assignment_to_model(db_assignment)


@router.post("/assignments/{assignment_id}/complete", response_model=Assignment)
async def complete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Mark an assignment as completed."""
    assignment = db.query(AssignmentTable).filter(AssignmentTable.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.is_completed = True
    assignment.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)
    return _assignment_to_model(assignment)


@router.post("/assignments/{assignment_id}/log-hours", response_model=Assignment)
async def log_assignment_hours(
    assignment_id: str,
    hours: float = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """Log hours worked on an assignment."""
    assignment = db.query(AssignmentTable).filter(AssignmentTable.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.hours_logged += hours
    db.commit()
    db.refresh(assignment)
    return _assignment_to_model(assignment)


from datetime import timedelta


def _course_to_model(table: CourseTable) -> Course:
    """Convert database table to Pydantic model."""
    return Course(
        id=table.id,
        code=table.code,
        name=table.name,
        day_of_week=table.day_of_week,
        start_time=time.fromisoformat(table.start_time),
        end_time=time.fromisoformat(table.end_time),
        location=table.location,
        semester_start=table.semester_start.date(),
        semester_end=table.semester_end.date(),
        excluded_dates=[date.fromisoformat(d) for d in (table.excluded_dates or [])],
        syllabus_path=table.syllabus_path,
        moodle_url=table.moodle_url,
        source_adapter=table.source_adapter,
        source_id=table.source_id,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


def _assignment_to_model(table: AssignmentTable) -> Assignment:
    """Convert database table to Pydantic model."""
    return Assignment(
        id=table.id,
        course_id=table.course_id,
        name=table.name,
        description=table.description,
        due_date=table.due_date,
        estimated_hours=table.estimated_hours,
        hours_logged=table.hours_logged,
        priority=Priority(table.priority),
        preferred_time_slots=[TimeSlotPreference(s) for s in (table.preferred_time_slots or [])],
        is_completed=table.is_completed,
        completed_at=table.completed_at,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )
