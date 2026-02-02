# Schedule Manager

An intelligent scheduling application that automatically manages your work projects, academic assignments, and household tasks using AI-powered time analysis.

## Features

- **Smart Scheduling**: LLM-powered task timing analysis ensures tasks are scheduled at logical times
- **Multiple Task Types**: Manage work projects, academic assignments, and household chores in one place
- **Google Integration**: Sync with Google Calendar and Google Sheets
- **Automatic Time Blocking**: Generates optimized schedules based on priorities and deadlines
- **Work/Life Balance**: Separates work hours from personal time
- **Intelligent Task Ordering**: Breakfast dishes in the morning, dinner tasks in the evening, etc.

## Quick Start

### Option 1: Docker (Recommended for sharing)

The easiest way to deploy Schedule Manager is using Docker:

```bash
# Start all services
docker-compose up -d

# Access the app
open http://localhost:4200
```

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for detailed Docker deployment instructions.

### Option 2: Local Development

#### Backend
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8765
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### Ollama (for LLM features)
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3:8b
ollama serve
```

## Tech Stack

- **Frontend**: Angular 18+ (Standalone components)
- **Backend**: FastAPI (Python 3.12)
- **Database**: SQLite
- **LLM**: Ollama with Llama 3 (8B model)
- **Integrations**: Google Calendar API, Google Sheets API
- **Desktop**: Electron (optional)

## Architecture

```
Frontend (Angular)
       ↓
Backend (FastAPI)
       ↓
   ┌───┴───┐
SQLite    Ollama (LLM)
```

## Key Features

### Intelligent Task Timing
Uses LLM to analyze task names and determine optimal scheduling times:
- **Morning tasks**: Breakfast preparation, morning dishes, making bed
- **Afternoon tasks**: Errands, grocery shopping, laundry
- **Evening tasks**: Dinner preparation, evening dishes
- **Flexible tasks**: General cleaning, vacuuming, organizing

### Work/Life Separation
- **Work Hours (8 AM - 4 PM)**: Dedicated to work projects
- **Personal Time**: After work and weekends for personal projects, assignments, and household tasks
- Prevents scheduling homework during work hours

### Multi-Source Data
- Manual entry through the UI
- Google Sheets sync for bulk task management
- Document parsing (PDF syllabi, research proposals) using Ollama

## Configuration

1. Copy `.env.example` to `.env`
2. Configure your Google OAuth credentials (optional)
3. Set up Google Sheets IDs (optional)
4. Adjust work hours and timezone

## License

MIT

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
