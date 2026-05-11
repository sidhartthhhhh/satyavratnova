# Gen Z Posts API

Small Django REST-ish service for users, posts, video upload URLs, trending feeds, Redis caching, and caption search.

The project demonstrates a practical backend architecture using Django, PostgreSQL, Redis, and LocalStack S3.

## Run Everything With Docker

```bash
docker compose up --build
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Docker starts:

- Django app
- PostgreSQL database
- Redis cache
- LocalStack S3 mock

LocalStack creates the `genz-media` bucket on startup.

## Local Setup Without Docker

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
export REDIS_URL=redis://localhost:6379/0
export AWS_STORAGE_BUCKET_NAME=genz-media
export AWS_S3_ENDPOINT_URL=http://localhost:4566
python manage.py migrate
python manage.py runserver
```

For a quick local smoke test without PostgreSQL:

```bash
USE_SQLITE=1 python manage.py migrate
USE_SQLITE=1 python manage.py runserver
```

## Database Schema

Migration files create:

- `users`: `id`, `username`, `email`, `created_at`
- `posts`: `id`, `user_id`, `caption`, `media_url`, `bitrate_status`, `timestamp`

Search/performance indexes:

- `posts_time_idx` for feed ordering
- `posts_caption_trgm_idx` PostgreSQL GIN trigram index for faster `caption ILIKE '%query%'` search

## Endpoints

- `GET /api/health/`
- `GET /api/users/`
- `POST /api/users/`
- `POST /api/media/presigned-url/`
- `GET /api/posts/?limit=20&offset=0`
- `POST /api/posts/`
- `GET /api/posts/<id>/`
- `DELETE /api/posts/<id>/`
- `GET /api/posts/trending/?hashtags=%23fyp,%23viral&limit=10`
- `GET /api/posts/trending/top10/`
- `GET /api/posts/search/?q=first&limit=10&offset=0`

## Media Upload Flow

Mobile clients first ask the API for an S3 presigned POST:

```bash
curl -X POST http://127.0.0.1:8000/api/media/presigned-url/ \
  -H "Content-Type: application/json" \
  -d '{"file_name":"demo.mp4","file_size":1048576}'
```

Validation happens before the presigned upload is created:

- only `.mp4` and `.m3u8`
- file size must be greater than `0`
- file size must be below `MAX_UPLOAD_BYTES`
- content type must match the extension

The response includes `upload_url`, `fields`, `s3_key`, and the eventual `media_url`.

## Feed Pagination

```bash
curl "http://127.0.0.1:8000/api/posts/?limit=10&offset=0"
```

The response includes `limit`, `offset`, `next_offset`, `total`, and `posts`.

## Redis Trending Cache

```bash
curl http://127.0.0.1:8000/api/posts/trending/top10/
```

This caches the top 10 trending posts in Redis for 60 seconds under `top10trending:v1`.

## Caption Search

```bash
curl "http://127.0.0.1:8000/api/posts/search/?q=first&limit=10&offset=0"
```

On PostgreSQL, migration `0002_indexes.py` enables `pg_trgm` and creates a GIN trigram index so Django's `icontains` search can use an efficient lookup strategy.

## Example Requests

```bash
curl -X POST http://127.0.0.1:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mira","email":"mira@example.com"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/posts/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"caption":"first post #fyp","media_url":"http://localhost:4566/genz-media/uploads/demo.mp4","bitrate_status":"ready"}'
```

## Postman

Import:

```text
postman_collection.json
```

Set `base_url` to `http://127.0.0.1:8000`.

## Submission Files

- Source code: this repo, ready to push to GitHub
- Postman collection: `postman_collection.json`
- Dockerized setup: `docker-compose.yml`
