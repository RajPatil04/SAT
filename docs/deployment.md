# Deployment Guide

SatQuery AI supports local development, remote FastAPI deployment, and containerized Docker environments.

## 1. Local Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
FastAPI server starts at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Vite development server starts at `http://localhost:3000`.

## 2. Docker Deployment
A complete `docker-compose.yml` is provided:
```bash
docker-compose up --build
```
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:3000`

## 3. Remote Model API Configuration
Specialist models hosted on Gradio, Hugging Face Spaces, or private cloud endpoints are configured through `backend/.env`.
Zero modifications to frontend code or client-side assets are necessary when changing hosting URLs.
