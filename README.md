# Seth Anandram Jaipuria School, Ved Campus – Barabanki — School Management System

A full-stack **Django + Django REST Framework** platform with role-based portals for **Admins, Teachers, Students and Parents**, a documented REST API, PDF report cards, CSV exports and a deployment-ready configuration (PostgreSQL, WhiteNoise, Gunicorn).

> A complete website + management system for the school: public website, and secure Admin, Teacher, Student and Parent portals backed by a documented REST API.

---

## Highlights

| Area | What's implemented |
|---|---|
| **Auth & RBAC** | Django `User` + Groups (Admin / Teacher / Student / Parent), PBKDF2 password hashing, group-based decorators, `403` on cross-role access |
| **Web portals** | Admin, Teacher, Student and Parent dashboards (server-rendered Django templates + Bootstrap) |
| **Academics** | Classes, subjects, attendance (bulk, per-class, per-day), study material, notices, video gallery, exams & results with automatic grading, weekly timetable |
| **Fees** | Payment ledger with balance validation, PDF receipts, reversible payments, fee dashboard with collection/outstanding totals |
| **Reports** | PDF report cards, PDF fee receipts (ReportLab), attendance CSV export |
| **REST API** | DRF ViewSets, JWT + Token + Session auth, pagination, search, filtering, ordering, validation, OpenAPI/Swagger docs |
| **Data privacy** | API never returns password hashes; students see only their own data, parents only their children's, teachers only their class |
| **Database** | SQLite locally, PostgreSQL in production via `DATABASE_URL` |
| **Data integrity** | Duplicate email / roll-number checks, upload type & size validation, safe deletes (class in use is protected), search + pagination on lists |
| **Quality** | 36 automated tests (auth, permissions, CRUD, API scoping, validation, PDF, CSV) |
| **Deployment** | `requirements.txt`, `Procfile`, WhiteNoise static files, env-based settings, HTTPS hardening when `DEBUG=False` |

## Roles & permissions

| Capability | Admin | Teacher | Student | Parent |
|---|:-:|:-:|:-:|:-:|
| Manage classes, subjects, teachers, students, parents, notices, video gallery (add / edit / delete) | ✅ | – | – | – |
| Attendance | ✅ view + CSV | ✅ bulk mark / edit / delete (own class) | own + % summary | children only |
| Study material | – | ✅ upload / delete | view | – |
| Create exams, enter results | ✅ (API) | ✅ (own class) | view own | view children's |
| Download PDF report card | – | – | ✅ own | ✅ children only |
| Fee ledger — record / reverse payments, PDF receipts | ✅ | – | view own | view children's |
| Weekly timetable | ✅ manage | view own class | view own class | view children's |
| Export attendance CSV | ✅ | – | – | – |
| Django admin site | ✅ | – | – | – |

## Tech stack
Python 3.12 · Django 5.1 · Django REST Framework · SimpleJWT · django-filter · drf-spectacular · ReportLab · WhiteNoise · Gunicorn · PostgreSQL / SQLite · Bootstrap 5

## Project structure
```
EduManage/   settings, root urls, role decorators
smsapp/       public website (news, video gallery, career, group), login/logout, enquiry form, setup_roles & seed_demo commands
adminapp/     admin portal + core models (Classes, Subject, Teacher, student, Parent, Attendance, Notification)
teacherapp/   teacher portal (profile, attendance, study material)
studentapp/   student portal (attendance, material, results, PDF report card)
parentapp/    parent portal (read-only, ownership-checked)
examapp/      Exam & Result models, teacher result entry, PDF generation
api/          DRF serializers, viewsets, permissions, routes, tests
```

## Getting started (local)
```bash
python3 -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_roles      # creates role groups, links existing users
python manage.py seed_demo        # optional demo parent / exam / results
python manage.py runserver
```
Open http://127.0.0.1:8000/ — login at `/login/`.

### Demo accounts
| Role | Email | Password |
|---|---|---|
| Admin | admin@gmail.com | admin |
| Teacher | anamika@gmail.com | 12345 |
| Student | bushra@gmail.com | 12345 |
| Parent | parent@gmail.com | 12345 |

*Change these before any public deployment.*

## REST API
- Interactive docs (Swagger): **`/api/docs/`** · OpenAPI schema: `/api/schema/`
- Base path: `/api/v1/`

| Endpoint | Notes |
|---|---|
| `POST /auth/token/` · `POST /auth/token/refresh/` | JWT login `{username, password}` |
| `GET /me/` | current user + roles |
| `/students/` `/teachers/` `/classes/` `/subjects/` | search, filter, ordering, pagination |
| `/attendance/` | filter by `sclass`, `status`, `created_date`, `sid` |
| `/exams/` `/results/` | results include computed `percentage` and `grade` |
| `/fee-payments/` `/timetable/` | role-scoped the same way as everything else |
| `/notifications/` | read: all users, write: admin |

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/token/ -H 'Content-Type: application/json' \
  -d '{"username":"admin@gmail.com","password":"admin"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")
curl -H "Authorization: Bearer $TOKEN" "localhost:8000/api/v1/students/?search=bushra&ordering=-rollno"
```

## Tests
```bash
python manage.py test        # 43 tests
```

## Deployment (Render / Railway / similar)
1. Create a PostgreSQL database and a web service from this repo.
2. Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
3. Start: `gunicorn EduManage.wsgi` (the `Procfile` also runs `migrate` + `setup_roles` on release).
4. Set environment variables from `.env.example` (`SMS_SECRET_KEY`, `SMS_DEBUG=False`, `SMS_ALLOWED_HOSTS`, `SMS_CSRF_ORIGINS`, `DATABASE_URL`).
5. **Uploaded media** (photos, notices, study material) needs persistent storage — attach a disk or move `MEDIA_ROOT` to S3/Cloudinary (Django serves `/media/` only when `DEBUG=True`).

## Screenshots
Add screenshots to a `docs/` folder and link them here (login, admin dashboard, teacher results entry, student dashboard, PDF report card, Swagger UI).

## Roadmap
- Replace string links (`Student.sclass`, `Teacher.tclass`) with `ForeignKey`s + typed `DateField`/`DecimalField`s
- Timetable, assignments, fee-receipt PDFs, email notifications
- Front-end SPA (React) consuming the existing API
