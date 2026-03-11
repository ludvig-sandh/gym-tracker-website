# gym-tracker-website
An application that my friends and I have been using to track our gym progress since 2022.
Written in Python with Flask.

## Setup

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

## Docker Compose
For a prod server deployment behind Nginx:

1. Create a local `.env` file on the server containing:

```bash
SECRET_KEY=replace-with-a-long-random-secret
HOST_BIND=127.0.0.1
HOST_PORT=5000
```

This key is used by Flask to securely sign session and other sensitive data.
`HOST_PORT` is the port nginx should proxy to on the server.

2. Start the app:

```bash
docker compose up -d --build
```

The container runs Gunicorn and mounts `./instance` to `/app/instance` so the SQLite database persists.
