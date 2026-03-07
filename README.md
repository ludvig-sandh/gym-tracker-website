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
