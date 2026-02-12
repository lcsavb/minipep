# minipep

Open-source Electronic Health Records (EHR) system for small clinics in Brazil.

## Product Overview

- **Target users:** Small clinics — solo practitioners or practices with a few doctors.
- **Roles:** Doctors (clinical work) and Recepcionistas (scheduling, front-desk).
- **Locale:** Brazil (CFM/CRM context). UI uses Django i18n to support pt-BR and English.
- **Clinical coding:** ICD / SNOMED for diagnoses — no data exchange protocols yet.

### Core Modules

1. **Encounter dashboard** — today's schedule, mark arrivals, track status (current).
2. **Anamnesis** — single free-text field per encounter for clinical notes.
3. **Prescriptions** — single free-text field per encounter.

## Tech Stack

- **Backend:** Django 6.0, Python 3.13
- **Database:** SQLite (dev)
- **Frontend:** Django templates + Tailwind CSS v4
- **Tailwind tooling:** Deno runs `@tailwindcss/cli`; Tailwind scans `core/templates/`

## Project Structure

```
minipep/          # Django project settings (settings.py, urls.py, wsgi/asgi)
core/             # Main app — models, views, urls, templates, admin, management commands
static/css/       # input.css (Tailwind source) → output.css (built)
```

## Key Commands

```bash
# Activate virtualenv
source venv/bin/activate

# Run dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Seed sample data (patients, doctors, today's encounters)
python manage.py seed_patients

# Tailwind — build or watch
deno task tw:build
deno task tw:watch
```

## Architecture Notes

- Custom User model (`core.User`) — email-based auth, no username field.
- Models: `User`, `Doctor` (1:1 with User), `Patient`, `Encounter` (FK to Patient + Doctor).
- Encounter statuses: scheduled → arrived → in_progress → completed | cancelled.
- Views are function-based, protected with `@login_required`.
- All URLs live in `core/urls.py`, included at root in `minipep/urls.py`.
- Django admin is registered for all models at `/admin/`.

## Conventions

- Keep views as simple function-based views unless complexity demands CBVs.
- Use Tailwind utility classes directly in templates — no custom CSS unless unavoidable.
- All Tailwind source is in `static/css/input.css`; never edit `output.css` directly.
- Run `deno task tw:build` after adding new Tailwind classes that aren't already in use.
- Use Django's i18n (`{% trans %}`, `gettext`) for all user-facing strings.
- Anamnesis and prescriptions are simple text fields — avoid over-structuring clinical data.
