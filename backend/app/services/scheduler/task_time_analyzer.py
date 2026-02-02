"""LLM-based task time analysis for intelligent scheduling."""

import json
import re
from datetime import time
from typing import Optional
import httpx


class TaskTimeAnalyzer:
    """Uses LLM to analyze household tasks and determine optimal scheduling times."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3:8b"

    def analyze_task_timing(self, task_name: str, task_description: Optional[str] = None) -> dict:
        """
        Analyze a task and determine its optimal time preferences.

        Returns:
            dict with:
                - preferred_time: "morning" | "afternoon" | "evening" | "anytime"
                - earliest_hour: int (24-hour format) - earliest sensible time
                - latest_hour: int (24-hour format) - latest sensible time
                - reasoning: str - explanation of the timing choice
        """
        prompt = self._build_timing_prompt(task_name, task_description)

        try:
            response = self._call_ollama(prompt)
            return self._parse_timing_response(response)
        except Exception as e:
            print(f"Error analyzing task timing for '{task_name}': {e}")
            # Fallback to anytime if LLM fails
            return {
                "preferred_time": "anytime",
                "earliest_hour": 9,
                "latest_hour": 21,
                "reasoning": "Default scheduling (LLM unavailable)"
            }

    def _build_timing_prompt(self, task_name: str, task_description: Optional[str] = None) -> str:
        """Build the prompt for task timing analysis."""
        description_text = f"\nDescription: {task_description}" if task_description else ""

        return f"""Analyze this household task and determine when it should logically be scheduled during the day.

Task: {task_name}{description_text}

Consider:
- Meal-related tasks (breakfast, lunch, dinner) should be near their respective meal times
- Morning tasks (making bed, breakfast dishes) should be in the morning
- Cleaning tasks can be flexible but should make logical sense
- Some tasks are time-sensitive (e.g., "breakfast dishes" should NOT be done at 7 PM)

IMPORTANT: Choose ONLY ONE preferred_time value. Do not use multiple values or separators like "|".
- If a task can be done at multiple times, use "anytime"
- If a task has a specific optimal time, choose the most appropriate single value

Respond in this EXACT JSON format (no extra text):
{{
  "preferred_time": "morning|afternoon|evening|anytime",
  "earliest_hour": <number 0-23>,
  "latest_hour": <number 0-23>,
  "reasoning": "<brief explanation>"
}}

Examples:
- "Breakfast dishes" → {{"preferred_time": "morning", "earliest_hour": 7, "latest_hour": 14, "reasoning": "Should be done shortly after breakfast or by early afternoon"}}
- "Dinner dishes" → {{"preferred_time": "evening", "earliest_hour": 18, "latest_hour": 21, "reasoning": "Should be done after dinner"}}
- "Laundry" → {{"preferred_time": "anytime", "earliest_hour": 9, "latest_hour": 21, "reasoning": "Flexible task that can be done throughout the day"}}
- "Make bed" → {{"preferred_time": "morning", "earliest_hour": 7, "latest_hour": 11, "reasoning": "Best done in the morning after waking up"}}

Respond only with the JSON, no other text."""

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API."""
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Low temperature for consistent results
                }
            )
            response.raise_for_status()
            return response.json()["response"]

    def _parse_timing_response(self, response: str) -> dict:
        """Parse the LLM response into structured timing data."""
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON found in response: {response}")

        try:
            data = json.loads(json_match.group())

            # Validate required fields
            required_fields = ["preferred_time", "earliest_hour", "latest_hour", "reasoning"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate time range
            if not (0 <= data["earliest_hour"] <= 23):
                raise ValueError(f"Invalid earliest_hour: {data['earliest_hour']}")
            if not (0 <= data["latest_hour"] <= 23):
                raise ValueError(f"Invalid latest_hour: {data['latest_hour']}")
            if data["earliest_hour"] > data["latest_hour"]:
                raise ValueError(f"earliest_hour > latest_hour")

            # Validate and clean preferred_time
            valid_times = ["morning", "afternoon", "evening", "anytime"]
            preferred_time = data["preferred_time"]

            # Handle cases where LLM returns multiple values like "morning|afternoon"
            if "|" in preferred_time or "/" in preferred_time:
                # Take the first value or map to "anytime"
                preferred_time = "anytime"
                data["preferred_time"] = preferred_time

            if data["preferred_time"] not in valid_times:
                raise ValueError(f"Invalid preferred_time: {data['preferred_time']}")

            return data

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse LLM response: {e}\nResponse: {response}")

    def enrich_tasks_with_timing(self, tasks: list) -> list:
        """
        Analyze a list of household tasks and enrich them with timing preferences.

        Args:
            tasks: List of HouseholdTask objects or dicts with 'name' and 'description'

        Returns:
            List of tasks with added 'timing_analysis' field
        """
        enriched_tasks = []

        for task in tasks:
            # Extract name and description from task object or dict
            if hasattr(task, 'name'):
                name = task.name
                description = task.description if hasattr(task, 'description') else None
            else:
                name = task.get('name', 'Unknown Task')
                description = task.get('description')

            # Analyze timing
            timing = self.analyze_task_timing(name, description)

            # Add timing to task
            if hasattr(task, '__dict__'):
                # If it's an object, add as attribute (won't persist, but useful for scheduling)
                task.timing_analysis = timing
            else:
                # If it's a dict, add as key
                task['timing_analysis'] = timing

            enriched_tasks.append(task)

        return enriched_tasks
