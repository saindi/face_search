# Face Search

[![CI](https://github.com/saindi/face_search/actions/workflows/ci.yml/badge.svg)](https://github.com/saindi/face_search/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Django 4.0](https://img.shields.io/badge/django-4.0-092E20.svg)](https://www.djangoproject.com/)

Face Search is a Django web service that identifies people on a photo by
matching detected faces against a database of known face encodings, and
returns the information linked to each match — identity documents
(passport, driver's license) and social media profiles (VK, OK, Telegram,
Facebook, Viber).

The project exposes both a web interface for interactive search and a REST
API for programmatic access and data ingestion.

> ⚠️ **Ethical & legal notice.** This software performs biometric
> identification of individuals from photographs and links them to personal
> data. It is intended for research, learning, and lawful use only (e.g. on
> data you own or are authorized to process). Identifying people without
> consent may violate privacy laws such as the GDPR. You are responsible for
> complying with all applicable laws in your jurisdiction.

## Features

- **Face detection & matching** — locates every face on an uploaded photo
  and compares it against the stored encodings using
  [`face_recognition`](https://github.com/ageitgey/face_recognition) (dlib).
- **Configurable match tolerance** — the strictness of the comparison can be
  tuned per request (`?tolerance=`), defaulting to a strict `0.45`.
- **Linked records** — each face can be associated with multiple sources
  (documents and social-media avatars) through a flexible relation table.
- **REST API** — JWT / token authenticated endpoints for identification and
  bulk data upload.
- **Database statistics** — counts of faces, documents and avatars with a
  per-source breakdown.
- **Face deletion** — remove a face together with all of its linked records.
- **Search audit log** — every identification request is recorded (user,
  time, faces detected, matches found).
- **Health check** — unauthenticated endpoint for monitoring / orchestration.

## Tech stack

- **Backend:** Django 4.0, Django REST Framework
- **Face recognition:** `face_recognition` 1.3 (dlib 19.24)
- **Database:** PostgreSQL
- **Auth:** SimpleJWT + DRF Token authentication
- **Infrastructure:** Docker Compose (web + db + nginx), Gunicorn

## Getting started

Clone the repository. Using a virtual environment to isolate dependencies is
recommended.

### Environment variables

The project reads configuration from a `.env.dev` file in the project root.
Create one with the following variables:

```dotenv
SECRET_KEY=your-secret-key
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]

POSTGRES_ENGINE=django.db.backends.postgresql
POSTGRES_NAME=face_search_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Local setup

Install dependencies (pip or poetry):

```shell
pip install -r requirements.txt
```

> Note: `dlib` requires CMake and a C++ build toolchain to compile.

Run migrations:

```shell
python manage.py migrate
```

Create a superuser:

```shell
python manage.py createsuperuser
```

Run the development server:

```shell
python manage.py runserver
```

### Docker

Bring the full stack (web, PostgreSQL, nginx) up with Docker Compose:

```shell
docker-compose up --build
```

The web app is served on port `8000` and proxied by nginx on port `80`.

## Web interface

| Path        | Description                                   |
|-------------|-----------------------------------------------|
| `/`         | Redirects to the search page                  |
| `/search/`  | Upload a photo and search for matches (login) |
| `/signin/`  | Sign in                                       |
| `/signup/`  | Sign up                                       |
| `/admin/`   | Django admin                                  |

## REST API

All endpoints are prefixed with `/api/`. Authenticated endpoints accept a
JWT (`Authorization: Bearer <token>`) or a DRF token
(`Authorization: Token <token>`).

| Method   | Endpoint            | Auth | Description                                                       |
|----------|---------------------|------|-------------------------------------------------------------------|
| `POST`   | `/api/token/`       | —    | Obtain a JWT access token (`username`, `password`)                |
| `POST`   | `/api/token-auth/`  | —    | Obtain a DRF auth token                                           |
| `GET`    | `/api/identify/`    | ✅   | Find matches for an uploaded `photo`. Optional `?tolerance=0.45`  |
| `POST`   | `/api/identify/`    | ✅   | Bulk upload data: a `photo` zip archive and an `info` text file   |
| `GET`    | `/api/stats/`       | ✅   | Database counts with per-source breakdown                         |
| `DELETE` | `/api/face/<id>/`   | ✅   | Delete a face and all of its linked documents / avatars           |
| `GET`    | `/api/health/`      | —    | Health check; `200` if the database is reachable, `503` otherwise |

### Data upload format

`POST /api/identify/` expects two files:

- `photo` — a `.zip` archive containing the face images.
- `info` — a `.txt` file where each line describes one record, fields
  separated by `[%]` and terminated by `[%]`:

  ```
  <source>[%]<id-or-number>[%]<name>[%]<image-filename-in-zip>[%]
  ```

  `source` must be one of the registered document sources
  (`passport`, `driver_license`) or avatar sources
  (`vk`, `ok`, `tg`, `fb`, `viber`).

## Data model

- **FaceModel** — stores a face encoding (128-dimensional vector serialized
  as a space-separated string).
- **RelatedModel** — links a face to a record in another table
  (`face_documentmodel` / `face_avatarmodel`) by `record_id`.
- **DocumentModel** — identity documents (source, number, name).
- **AvatarModel** — social-media profiles (source, profile id, name).
- **SearchLog** — audit record of each identification request.

## Project structure

```
face_search/        # Django project settings, URLs, WSGI/ASGI
├── api/            # REST API (views, serializers, urls)
├── face/           # Core domain: models, web views, admin, migrations
├── user/           # Custom user model and auth views
├── client/         # Standalone data-loading client (psycopg2, no Django)
├── services.py     # Face comparison business logic (FaceCompare)
├── nginx/          # nginx reverse-proxy config
└── docker-compose.yml
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE)
file for details.
