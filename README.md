# gym-tracker-website
A website that lets you track gym progress, written in Python with Flask

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Docker

```bash
docker build -t gym-tracker-website .
docker run --rm -p 5000:5000 gym-tracker-website
```

## Docker Compose

For a server setup behind Nginx:

```bash
docker compose up -d --build
```

This compose file:
- binds the app to `127.0.0.1:5000` on the host
- mounts `./instance` to `/app/instance` so the SQLite database persists
- restarts the container automatically unless you stop it manually

To stop it:

```bash
docker compose down
```
