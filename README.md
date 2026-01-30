# Schedule Manager

A desktop application for automatic time blocking across work, academic, and household tasks. Integrates with Google Calendar and Google Sheets to dynamically build your daily schedule.

## Features

- Sync with Google Calendar for existing commitments
- Pull tasks from Google Sheets (household, personal, work, academic)
- Automatic schedule generation based on priorities and preferences
- Protected time blocks for gym, meals, etc.
- Desktop app via Electron with Angular frontend and FastAPI backend

## Prerequisites

- **Node.js** 18.0.0 or higher
- **Python** 3.11 or higher
- **Poetry** (Python dependency manager)
- **Google Cloud account** with a project set up

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it (e.g., "Schedule Manager") and click "Create"
4. Select your new project from the dropdown

### 2. Enable Required APIs

1. Go to **APIs & Services** → **Library**
2. Search for and enable each of these APIs:
   - **Google Calendar API**
   - **Google Sheets API**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (unless you have a Google Workspace org)
3. Fill in the required fields:
   - App name: `Schedule Manager`
   - User support email: your email
   - Developer contact: your email
4. Click "Save and Continue"
5. On the **Scopes** page, click "Add or Remove Scopes" and add:
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/spreadsheets.readonly`
6. Click "Save and Continue"
7. On **Test users**, add your Google account email
8. Click "Save and Continue" → "Back to Dashboard"

### 4. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Desktop app**
4. Name: `Schedule Manager Desktop`
5. Click "Create"
6. **Download the JSON file** and save it as `google_credentials.json` in the project root

You'll get a Client ID and Client Secret - copy these for your `.env` file.

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd schedule-manager

# Install all dependencies
npm run install:all

# Create your environment file
npm run setup
```

## Configuration

Edit the `.env` file with your values:

```bash
# Required: From Google Cloud Console (step 4 above)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_CREDENTIALS_PATH=./google_credentials.json

# Required: Your Google Calendar ID
# Usually your Gmail address, or find it in:
# Google Calendar → Settings → [Your Calendar] → "Integrate calendar" → Calendar ID
GOOGLE_CALENDAR_ID=your-email@gmail.com

# Google Sheets IDs (get from the URL of each sheet)
# URL format: https://docs.google.com/spreadsheets/d/{THIS_IS_THE_ID}/edit
HOUSEHOLD_SHEET_ID=1ABC123...
PERSONAL_SHEET_ID=1DEF456...
ACADEMIC_SHEET_ID=1GHI789...

# Your timezone
TIMEZONE=America/New_York

# Work hours (24h format)
WORK_START_HOUR=9
WORK_END_HOUR=17

# Protected time blocks (optional)
# Format: "HH:MM-HH:MM,HH:MM-HH:MM"
PROTECTED_HOURS=12:00-13:00,18:00-19:00
```

### Finding Your Google Sheet ID

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit`
3. The ID is the long string between `/d/` and `/edit`: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ`

## Running the App

```bash
# Development mode (backend + frontend)
npm run dev

# Full stack with Electron desktop app
npm run dev:full
```

The dev server will start:
- **API**: http://localhost:8765
- **Web**: http://localhost:4200

## Project Structure

```
schedule-manager/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # Data models
│   │   ├── services/ # Business logic
│   │   └── config.py # Settings
│   └── pyproject.toml
├── frontend/         # Angular 19 web app
│   └── src/app/
│       ├── features/ # Page components
│       └── core/     # Services
├── electron/         # Desktop app wrapper
├── .env.example      # Environment template
└── package.json      # Workspace scripts
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start backend + frontend for development |
| `npm run dev:full` | Start full stack including Electron |
| `npm run backend:dev` | Start only the FastAPI backend |
| `npm run frontend:dev` | Start only the Angular frontend |
| `npm run install:all` | Install all dependencies |
| `npm run setup` | Create .env from template |

## First Run Authentication

On first run, the app will open a browser window for Google OAuth authentication. Sign in with the Google account you added as a test user and grant the requested permissions. The token will be cached at `~/.schedule-manager/google_token.json`.

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure you downloaded the OAuth credentials as a Desktop app type, not Web app
- Verify the credentials JSON file path in your `.env`

### "Error 403: access_denied"
- Add your email to the test users in Google Cloud Console OAuth consent screen

### "Google Sheets API has not been enabled"
- Go to Google Cloud Console → APIs & Services → Library → Enable Google Sheets API

### Backend won't start
```bash
# Make sure Poetry is installed
pip install poetry

# Reinstall backend dependencies
cd backend && poetry install
```

## License

MIT
