#!/bin/bash

# Schedule Manager - Quick Start Script
set -e

echo "🗓️  Schedule Manager - Starting Up..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running in production!"
fi

# Build and start containers
echo "🏗️  Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"

    # Check if llama3:8b model exists
    if curl -s http://localhost:11434/api/tags | grep -q "llama3:8b"; then
        echo "✅ Llama3:8b model is already installed"
    else
        echo "📥 Pulling Llama3:8b model (this may take a few minutes)..."
        docker exec -it schedule-manager-ollama ollama pull llama3:8b
        echo "✅ Llama3:8b model installed"
    fi
else
    echo "⚠️  Ollama service is not responding yet. Run 'make setup-ollama' later to install the model."
fi

# Check if backend is healthy
echo "🔧 Checking backend service..."
if curl -s http://localhost:8765/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not responding yet. Give it a moment to start up."
fi

# Check if frontend is accessible
echo "🎨 Checking frontend service..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:4200 | grep -q "200"; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend is not responding yet. Give it a moment to start up."
fi

echo ""
echo "✨ Schedule Manager is starting up!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:4200"
echo "   Backend:   http://localhost:8765"
echo "   API Docs:  http://localhost:8765/docs"
echo ""
echo "📚 Useful commands:"
echo "   View logs:        make logs"
echo "   Stop services:    make down"
echo "   Restart services: make restart"
echo "   Check health:     make health"
echo ""
echo "📖 For more information, see DOCKER_SETUP.md"
