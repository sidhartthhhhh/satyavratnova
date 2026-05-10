# Gen Z Posts API

Small Django REST-ish service for users and posts.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PostgreSQL is the default database.

```bash
export POSTGRES_DB=genz_posts
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
python manage.py migrate
python manage.py runserver
```

For a quick local smoke test without PostgreSQL:

```bash
USE_SQLITE=1 python manage.py migrate
USE_SQLITE=1 python manage.py runserver
```

## PostgreSQL Schema

Django migration `api/migrations/0001_initial.py` creates:

- `users`: `id`, `username`, `email`, `created_at`
- `posts`: `id`, `user_id`, `caption`, `media_url`, `bitrate_status`, `timestamp`

## Endpoints

- `GET /api/health/`
- `GET /api/users/`
- `POST /api/users/`
- `GET /api/posts/`
- `POST /api/posts/`
- `GET /api/posts/<id>/`
- `DELETE /api/posts/<id>/`
- `GET /api/posts/trending/?hashtags=#fyp,#viral&limit=10`

## Example Requests

```bash
curl -X POST http://127.0.0.1:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mira","email":"mira@example.com"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"caption":"first post #fyp","media_url":"https://s3.amazonaws.com/bucket/video.mp4","bitrate_status":"ready"}'
```
