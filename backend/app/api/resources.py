"""API endpoints for parsing and managing resource documents."""

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.tables import AssignmentTable, ProjectTable, CourseTable
from app.services.parsers.document_parser import DocumentParser

router = APIRouter()


@router.post("/parse")
async def parse_resources_directory(
    resources_path: str = "../resources",
    db: Session = Depends(get_db),
):
    """
    Parse all documents in the resources directory and create tasks/assignments.

    This endpoint:
    1. Parses PDFs and DOCX files using Ollama
    2. Extracts tasks, assignments, and deadlines
    3. Creates appropriate database entries (Assignments, Projects, etc.)

    Args:
        resources_path: Path to resources directory
        db: Database session

    Returns:
        Summary of parsed documents and created tasks
    """
    parser = DocumentParser()

    # Parse all documents
    try:
        parsed_documents = await parser.parse_resources_directory(resources_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse documents: {str(e)}")

    if not parsed_documents:
        return {
            "message": "No documents found or parsed",
            "documents_parsed": 0,
            "tasks_created": 0,
        }

    # Process each document and create database entries
    tasks_created = 0
    assignments_created = []
    projects_created = []

    for doc_name, tasks in parsed_documents.items():
        # Determine if this is a syllabus (create course + assignments)
        # or research proposal (create project + milestones)

        if "syllabus" in doc_name.lower():
            # Create or find course
            course_name = _extract_course_name(doc_name)
            course = db.query(CourseTable).filter(CourseTable.name == course_name).first()

            if not course:
                # Set default course schedule (will be updated manually later)
                course = CourseTable(
                    id=str(uuid4()),
                    name=course_name,
                    code=_extract_course_code(doc_name),
                    day_of_week=1,  # Default to Tuesday
                    start_time="10:00",  # Default time
                    end_time="11:30",
                    semester_start=datetime.now(),
                    semester_end=datetime.now() + timedelta(days=120),  # ~4 months
                    syllabus_path=str(Path(resources_path) / doc_name),
                )
                db.add(course)
                db.flush()  # Get the course ID

            # Create assignments for this course
            for task in tasks:
                try:
                    due_date = datetime.fromisoformat(task.get('due_date', '2026-12-31'))
                except:
                    due_date = datetime.now() + timedelta(days=30)

                assignment = AssignmentTable(
                    id=str(uuid4()),
                    course_id=str(course.id),
                    name=task.get('name', 'Unnamed Assignment'),
                    description=task.get('description', ''),
                    due_date=due_date,
                    estimated_hours=task.get('estimated_hours', 5),
                    priority=task.get('priority', 'medium'),
                )
                db.add(assignment)
                assignments_created.append(task.get('name'))
                tasks_created += 1

        elif "proposal" in doc_name.lower() or "research" in doc_name.lower():
            # Create a research project
            project_name = _extract_project_name(doc_name)
            project = db.query(ProjectTable).filter(ProjectTable.name == project_name).first()

            if not project:
                # Sum up all estimated hours for total allocation
                total_hours = sum(task.get('estimated_hours', 5) for task in tasks)

                project = ProjectTable(
                    id=str(uuid4()),
                    name=project_name,
                    description=f"Research project from {doc_name}",
                    total_hours_allocated=total_hours,
                    hours_used=0,
                    allocation_percentage=25.0,  # Default 25%
                    priority="high",
                    is_active=True,
                    source_adapter='document_parser',
                    source_id=doc_name,
                )
                db.add(project)
                projects_created.append(project_name)
                tasks_created += 1

        else:
            # Generic document - create as general project
            project_name = Path(doc_name).stem
            total_hours = sum(task.get('estimated_hours', 5) for task in tasks)

            project = ProjectTable(
                id=str(uuid4()),
                name=project_name,
                description=f"Project from {doc_name}",
                total_hours_allocated=total_hours,
                hours_used=0,
                allocation_percentage=10.0,
                priority="medium",
                is_active=True,
                source_adapter='document_parser',
                source_id=doc_name,
            )
            db.add(project)
            projects_created.append(project_name)
            tasks_created += len(tasks)

    # Commit all changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save tasks: {str(e)}")

    return {
        "message": "Resources parsed successfully",
        "documents_parsed": len(parsed_documents),
        "tasks_created": tasks_created,
        "assignments_created": assignments_created,
        "projects_created": projects_created,
        "details": {doc: len(tasks) for doc, tasks in parsed_documents.items()},
    }


def _extract_course_name(filename: str) -> str:
    """Extract course name from syllabus filename."""
    # Example: "ST 778 Syllabus.pdf" -> "ST 778"
    import re

    match = re.search(r'([A-Z]+\s*\d+)', filename)
    if match:
        return match.group(1)
    return Path(filename).stem


def _extract_course_code(filename: str) -> str:
    """Extract course code from syllabus filename."""
    import re

    match = re.search(r'([A-Z]+)\s*(\d+)', filename)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return ""


def _extract_project_name(filename: str) -> str:
    """Extract project name from document filename."""
    # Remove extension and clean up
    name = Path(filename).stem
    name = name.replace('_', ' ').replace('-', ' ')
    return name.title()
