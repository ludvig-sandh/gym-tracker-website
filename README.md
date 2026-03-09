# gym-tracker-website
A website that lets you track gym progress, written in Python with Flask

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
```

This key is used by Flask to securely sign session and other sensitive data.

2. Start the app:

```bash
docker compose up -d --build
```

The compose file mounts `./instance` to `/app/instance` so the SQLite database persists
