# minipep

Open-source Electronic Health Records (EHR) system for small clinics in Brazil.

## Prerequisites

- Python 3.13+
- [Deno](https://deno.land/) (for Tailwind CSS builds)

## Setup

Clone the repo and create a virtual environment:

```bash
git clone <repo-url>
cd minipep
python -m venv venv
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install django==6.0.2
```

Run migrations and (optionally) seed sample data:

```bash
python manage.py migrate
python manage.py seed_patients   # creates sample patients, doctors, and today's encounters
```

Build Tailwind CSS:

```bash
deno task tw:build
```

Create a superuser to access the admin and the app:

```bash
python manage.py createsuperuser
```

## Running the dev server

```bash
source venv/bin/activate
python manage.py runserver
```

Then open http://127.0.0.1:8000/. The Django admin is at http://127.0.0.1:8000/admin/.

To auto-rebuild CSS while developing templates, run in a separate terminal:

```bash
deno task tw:watch
```
