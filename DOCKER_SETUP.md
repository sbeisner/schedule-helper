# Schedule Manager - Docker Setup

This guide will help you deploy Schedule Manager using Docker.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB of free disk space (for Ollama model)

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd schedule-manager
```

### 2. Set up environment variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings (see Configuration section below).

### 3. Start the application

```bash
docker-compose up -d
```

This will:
- Build the frontend and backend containers
- Pull and start Ollama with the llama3:8b model (this may take 5-10 minutes on first run)
- Create persistent volumes for data storage

### 4. Access the application

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8765
- **API Documentation**: http://localhost:8765/docs

### 5. Set up Google OAuth (Optional)

If you want to sync with Google Calendar and Google Sheets:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Calendar API
   - Google Sheets API
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download the credentials JSON file
6. Copy the credentials file to the schedule data volume:

```bash
# Copy credentials to the Docker volume
docker cp credentials.json schedule-manager-backend:/data/credentials.json
```

7. Run the OAuth flow:

```bash
# This will print a URL - open it in your browser to authorize
docker exec -it schedule-manager-backend python -m app.services.google.auth_setup
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database
DATABASE_PATH=/data/data.db

# Google OAuth (optional)
GOOGLE_CREDENTIALS_PATH=/data/credentials.json
GOOGLE_TOKEN_PATH=/data/google_token.json

# Google Sheets (optional - configure in the UI instead)
HOUSEHOLD_SHEET_ID=your_sheet_id_here

# Ollama
OLLAMA_URL=http://ollama:11434

# Backend settings
DEBUG=false
```

## Managing the Application

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
```

### Stop the application

```bash
docker-compose down
```

### Stop and remove all data

```bash
docker-compose down -v
```

### Restart a service

```bash
docker-compose restart backend
```

### Update the application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose up -d --build
```

## Data Persistence

Data is stored in Docker volumes:

- `schedule-data`: Contains the SQLite database and Google OAuth tokens
- `ollama-data`: Contains the Ollama models

To backup your data:

```bash
# Backup the schedule data
docker run --rm -v schedule-manager_schedule-data:/data -v $(pwd):/backup alpine tar czf /backup/schedule-data-backup.tar.gz /data

# Restore from backup
docker run --rm -v schedule-manager_schedule-data:/data -v $(pwd):/backup alpine tar xzf /backup/schedule-data-backup.tar.gz -C /
```

## Troubleshooting

### Ollama model not loading

If the Ollama service fails to pull the model on first startup:

```bash
# Manually pull the model
docker exec -it schedule-manager-ollama ollama pull llama3:8b
```

### Backend can't connect to Ollama

Ensure the Ollama service is running and healthy:

```bash
docker-compose ps ollama
docker-compose logs ollama

# Test Ollama
curl http://localhost:11434/api/tags
```

### Frontend can't reach backend

Check that the backend is running and healthy:

```bash
curl http://localhost:8765/health
```

### Permission issues with volumes

If you encounter permission issues with mounted volumes:

```bash
# Fix ownership
docker-compose down
sudo chown -R $USER:$USER ./backend ./frontend
docker-compose up -d
```

## Production Deployment

For production deployment:

1. Use a reverse proxy (nginx, Caddy, Traefik) with SSL/TLS
2. Set up proper domain names
3. Configure environment variables for production
4. Enable firewall rules
5. Set up automated backups
6. Monitor logs and health checks

Example nginx reverse proxy configuration:

```nginx
server {
    listen 443 ssl http2;
    server_name schedule.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:4200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Architecture

```
┌─────────────┐
│  Browser    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Frontend   │  (Angular + Nginx)
│  Port: 4200 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Backend    │  (FastAPI + Python)
│  Port: 8765 │
└──────┬──────┘
       │
       ├─────────────┐
       ▼             ▼
┌─────────────┐  ┌─────────────┐
│  SQLite DB  │  │   Ollama    │  (LLM for task analysis)
│  (Volume)   │  │  Port: 11434│
└─────────────┘  └─────────────┘
```

## Support

For issues or questions, please open an issue on GitHub.
