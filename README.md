# Django Backendfor ZeissGPT

# Project Overview

This project provides a Django-based backend that facilitates chat sessions between users and an AI assistant. It includes various endpoints for managing chat sessions, retrieving chat histories, and interacting with the AI.

# Tech Stack
•	Backend: Django
•	Containerization: Docker
•	Database: SQLite (local file-based database)
•	AI Integration: Uses OpenAI models through Azure API

# Requirements
•	Docker and Docker Compose installed

# Setup & Installation

1.	Clone the Repository
2.	Environment Variables
Create a .env file in the project root with the necessary configurations. Required variables include:
•	SECRET_KEY: Django’s secret key
•	AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY: Credentials for accessing the Azure OpenAI API
3.	Build and Run the Docker Container
```bash
docker-compose up --build
```
4.	Initialize the SQLite database locally by running migrations:
```bash
python manage.py makemigrations
python manage.py migrate 
```
5.	Create a Superuser to access the Django admin interface:
```bash
docker-compose exec web python manage.py createsuperuser
```
6. Configure a User and a the correct endpoint name for an azure openai instance.
7.	Accessing the API
    The API will be available at http://localhost:8000.

# API Endpoints
•	Authentication & Setup
•	api/check-authentication/: Verifies if the user is authenticated.
•	api/set-csrf-token/: Sets the CSRF token.

•	Chat Management
•	api/create-chat/: Creates a new chat session.
•	api/list-chats/: Lists all chat sessions for the user.
•	api/chat-history/<uuid:chat_id>/: Retrieves chat history for a specific session.
•	api/delete-chat/<uuid:chat_id>/: Deletes a chat session and creates a new one if none exist.
•	api/regenerate-message/<uuid:chat_id>/: Regenerates the last AI message in a chat session.

•	AI Interaction
•	api/generate-response/: Generates a response from the AI based on a user message.
•	api/get-options/: Retrieves available AI models and temperature options.

•	Other
•	api/get-weather/: Fetches weather data for specified latitude and longitude.

# Common Commands

•	Starting the Dev Container
```bash
docker-compose up
```
•	Stopping the Dev Container
```bash
docker-compose down
```
•	Rebuilding the Dev Container
```bash
docker-compose up --build
```

# Testing
Run tests to verify the setup and functionality:
``` bash
docker-compose exec web python manage.py test
```

# Troubleshooting
• OpenAI API Errors:
Ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are properly configured in .env.

Known Issues
•   Minimal test coverage