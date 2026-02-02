"""Document parser service using Ollama for extracting tasks from PDFs and DOCX files."""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import PyPDF2
import docx
import httpx


class DocumentParser:
    """Service for parsing documents and extracting tasks using Ollama."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3:8b"

    async def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n\n".join(text)
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return ""

    def parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n\n".join(text)
        except Exception as e:
            print(f"Error parsing DOCX {file_path}: {e}")
            return ""

    async def extract_tasks_with_ollama(self, document_text: str, document_type: str) -> list[dict]:
        """
        Use Ollama to extract structured task information from document text.

        Args:
            document_text: The full text of the document
            document_type: Type of document (syllabus, research_proposal, etc.)

        Returns:
            List of task dictionaries with name, description, due_date, estimated_hours, priority
        """
        prompt = self._build_extraction_prompt(document_text, document_type)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '{}')

                    # Parse JSON response
                    try:
                        tasks_data = json.loads(response_text)
                        return tasks_data.get('tasks', [])
                    except json.JSONDecodeError:
                        # Fallback: try to extract JSON from text
                        return self._extract_json_from_text(response_text)
                else:
                    print(f"Ollama API error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return []

    def _build_extraction_prompt(self, document_text: str, document_type: str) -> str:
        """Build prompt for Ollama based on document type."""

        if document_type == "syllabus":
            return f"""Analyze this course syllabus and extract all assignments, exams, projects, and deadlines.

For each task, provide realistic work estimates considering:
- Assignment complexity and typical graduate/undergraduate workload
- How many focused work sessions would be needed (e.g., "3 sessions of 2 hours each")
- Total time including research, writing, and revision

For each task, provide:
- name: Brief name of the assignment/exam
- description: Details about what's required
- due_date: Due date in YYYY-MM-DD format (if mentioned, otherwise estimate based on week number)
- estimated_hours: TOTAL hours needed (e.g., if 3 sessions of 2 hours = 6 hours total)
- work_sessions: How many focused sessions recommended (e.g., 3)
- session_duration: Hours per session (e.g., 2.0)
- priority: high/medium/low based on weight/importance
- type: assignment, exam, project, reading, or other

Example: A complex statistics assignment might need "3 sessions of 2.5 hours each" = 7.5 total hours

Document text:
{document_text}

Return ONLY a valid JSON object in this exact format:
{{
  "tasks": [
    {{
      "name": "Assignment 1: Statistical Inference",
      "description": "Complete problem set covering hypothesis testing and confidence intervals",
      "due_date": "2026-02-15",
      "estimated_hours": 8,
      "work_sessions": 3,
      "session_duration": 2.5,
      "priority": "high",
      "type": "assignment"
    }}
  ]
}}"""

        elif document_type == "research_proposal":
            return f"""Analyze this research proposal and extract all tasks, milestones, and deliverables.

For each major task, break it down into realistic work sessions:
- Consider that deep research work typically needs 2-3 hour focused sessions
- Literature reviews might need 5-8 sessions of 2-3 hours each
- Data analysis might need 4-6 sessions of 2-4 hours each
- Writing tasks might need 3-5 sessions of 2-3 hours each

For each task, provide:
- name: Brief name of the task/milestone
- description: Details about what needs to be done
- due_date: Estimated completion date in YYYY-MM-DD format
- estimated_hours: TOTAL hours needed
- work_sessions: Number of focused sessions recommended
- session_duration: Hours per session
- priority: high/medium/low based on importance
- type: research, writing, analysis, data_collection, or literature_review

Document text:
{document_text}

Return ONLY a valid JSON object in this exact format:
{{
  "tasks": [
    {{
      "name": "Literature Review",
      "description": "Comprehensive review of existing research on statistical methods",
      "due_date": "2026-03-01",
      "estimated_hours": 18,
      "work_sessions": 6,
      "session_duration": 3.0,
      "priority": "high",
      "type": "literature_review"
    }}
  ]
}}"""

        else:
            return f"""Analyze this document and extract all actionable tasks, deliverables, and deadlines.

For each task, provide:
- name: Brief name of the task
- description: Details about the task
- due_date: Due date in YYYY-MM-DD format (estimate if not specified)
- estimated_hours: Estimated hours to complete
- priority: high/medium/low
- type: General category

Document text:
{document_text}

Return ONLY a valid JSON object in this exact format:
{{
  "tasks": [
    {{
      "name": "Task name",
      "description": "Task description",
      "due_date": "2026-02-01",
      "estimated_hours": 5,
      "priority": "medium",
      "type": "task"
    }}
  ]
}}"""

    def _extract_json_from_text(self, text: str) -> list[dict]:
        """Attempt to extract JSON from text that may contain other content."""
        try:
            # Find JSON object in text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                data = json.loads(json_str)
                return data.get('tasks', [])
        except Exception as e:
            print(f"Could not extract JSON from text: {e}")
        return []

    async def parse_resources_directory(self, resources_path: str) -> dict[str, list[dict]]:
        """
        Parse all documents in the resources directory.

        Returns:
            Dictionary mapping file names to extracted tasks
        """
        resources_dir = Path(resources_path)
        if not resources_dir.exists():
            print(f"Resources directory not found: {resources_path}")
            return {}

        results = {}

        for file_path in resources_dir.glob('*'):
            if file_path.is_file():
                file_name = file_path.name
                extension = file_path.suffix.lower()

                print(f"Parsing {file_name}...")

                # Extract text based on file type
                if extension == '.pdf':
                    text = await self.parse_pdf(str(file_path))
                elif extension in ['.docx', '.doc']:
                    text = self.parse_docx(str(file_path))
                else:
                    print(f"Skipping unsupported file type: {extension}")
                    continue

                if not text:
                    print(f"No text extracted from {file_name}")
                    continue

                # Determine document type from filename
                doc_type = self._infer_document_type(file_name.lower())

                # Extract tasks using Ollama
                tasks = await self.extract_tasks_with_ollama(text, doc_type)

                if tasks:
                    results[file_name] = tasks
                    print(f"Extracted {len(tasks)} tasks from {file_name}")
                else:
                    print(f"No tasks extracted from {file_name}")

        return results

    def _infer_document_type(self, filename: str) -> str:
        """Infer document type from filename."""
        filename_lower = filename.lower()

        if 'syllabus' in filename_lower:
            return 'syllabus'
        elif 'proposal' in filename_lower or 'research' in filename_lower:
            return 'research_proposal'
        elif 'assignment' in filename_lower:
            return 'assignment'
        elif 'project' in filename_lower:
            return 'project'
        else:
            return 'general'
