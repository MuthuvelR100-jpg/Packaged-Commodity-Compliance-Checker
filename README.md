# AI-Powered Packaged Commodity Compliance Checker

A compliance-assistance and screening tool for packaged commodities sold in India.

This repository is being built incrementally. The first phase establishes the application boundaries and a runnable backend health check. It does not make legal decisions and does not yet process images or OCR.

## Architecture

- `frontend/`: React client, user workflows, dashboards, reports, and admin screens.
- `backend/`: Flask REST API, image/OCR pipeline, extraction services, rule engine, persistence, and reports.
- `backend/rule_engine/`: deterministic validation and scoring. Legal requirements must come from versioned, administrator-maintained rules rather than an AI model.
- `backend/database/`: SQLAlchemy models and database setup.
- `uploads/`: local development upload storage; do not commit user images.
- `reports/`: local development report output; do not commit generated reports.
- `tests/`: backend and frontend tests.

## Phase 1 prerequisites

Install:

- Python 3.11 or newer
- Node.js 20 LTS or newer and npm
- Git

Recommended tools:

- VS Code
- A current browser with camera permissions support

## Phase 1 setup

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

If PowerShell blocks script activation, use `\.venv\Scripts\python.exe` directly or adjust the execution policy for your user account.

## Run the Phase 1 backend

```powershell
.\.venv\Scripts\Activate.ps1
python backend\app.py
```

The API listens on `http://127.0.0.1:5000`. In another terminal, verify it:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

Expected response:

```text
status   phase
------   -----
ok       4
```

### Phase 15 API routes

The application now includes a responsive inspection workspace, searchable persisted history, downloadable PDF reports, and session-protected administration connected to the upload, preprocessing, OCR, extraction, validation, and scoring pipeline. The Flask backend uses an application factory, centralized configuration, route blueprints, SQLite persistence through SQLAlchemy, secure image upload handling, OpenCV preprocessing, PaddleOCR integration, deterministic declaration extraction, and a versioned rule catalog:

- `GET /api/health` - service status
- `GET /api/dashboard` - persisted dashboard metrics
- `GET /api/inspections` - saved inspection collection
- `GET /api/inspections?q=...&status=...&category=...` - filtered inspection history
- `POST /api/inspection` - save an inspection draft
- `GET /api/inspection/<id>` - persisted inspection details
- `DELETE /api/inspection/<id>` - delete a saved inspection record
- `GET /api/report/<id>` - generate and download a PDF screening report
- `POST /api/upload` - validate and store a package image as multipart form data using the `image` field
- `POST /api/preprocess` - preprocess a stored image using its generated `filename` and return quality metrics
- `POST /api/ocr` - run PaddleOCR on a processed image and return text, boxes, and confidence values
- `POST /api/extract` - normalize OCR text and extract structured declaration fields
- `POST /api/validate` - validate extracted fields against active, versioned category rules
- `POST /api/score` - calculate a transparent score and final screening status from validation results
- `GET /api/rules` - saved rule collection
- `GET /api/rules?category=food` - rules filtered by product category
- `POST /api/rules` - add a rule record
- `GET /api/categories` - supported active product categories
- `POST /api/auth/login` - start an authenticated session
- `POST /api/auth/logout` - end the current session
- `GET /api/auth/me` - inspect the current session user
- `POST /api/auth/users` - create a user; admin session required
- `PUT /api/rules/<id>` - update a rule; admin session required
- `DELETE /api/rules/<id>` - disable a rule; admin session required

Uploads accept JPG, JPEG, PNG, and WEBP files up to 10 MB. File contents are verified with Pillow and stored using generated UUID filenames. Preprocessing preserves the original, creates a sharpened grayscale derivative, measures blur and resolution, and reports `good`, `acceptable`, or `poor` quality. OCR is now connected through a lazy PaddleOCR adapter; rule validation, authentication, and report generation remain future phases.

### OCR runtime setup

PaddleOCR also requires a compatible PaddlePaddle runtime for the selected operating system and Python version. Install both using the current official PaddlePaddle installation command for your platform, then install the declared dependencies again:

```powershell
python -m pip install paddlepaddle
python -m pip install -r backend\requirements.txt
```

If the runtime is unavailable, `POST /api/ocr` returns HTTP `503` with code `OCR_UNAVAILABLE`; the API remains usable for upload, preprocessing, and text extraction from supplied OCR output. Rules require a category, source reference, and rule version; no legal rule is seeded automatically without verified source data. Validation returns `REVIEW` when no active rules exist for a category. Scoring is a screening aid and does not replace legal verification.

For the Windows CPU runtime, the OCR adapter disables PaddleOCR MKL-DNN/oneDNN acceleration because some PaddlePaddle versions can raise a PIR runtime-attribute error in that execution path. OCR continues using CPU inference.

The frontend's **New inspection** view runs the stages in order: upload, preprocess, OCR, field extraction, rule validation, and score. It displays the selected image, category, live stage progress, OCR confidence, declaration statuses, explanations, score, and screening status. Camera capture remains a browser input enhancement for the next UI iteration.

The frontend's **Inspection history** view loads persisted records, supports product search, status/category filters, detail selection, declaration display, and delete confirmation. Authentication and role-based permissions remain future hardening work; the current delete route is intended for local development.

The PDF report includes inspection metadata, uploaded image when available, extracted declarations, OCR confidence, rule-set version, status, score, and the automated-screening disclaimer.

The Rules Library is populated on startup from the preliminary mappings in `backend/database/seed.py`. Each record is labeled `Rules 2011.pdf`, carries its PDF rule reference in the description, and uses version `2011-preliminary`. Food and cosmetics exception mappings are displayed as `Verify separately` and are inactive until the referenced sector-specific requirements are verified.

### Admin setup

Set `ADMIN_EMAIL`, `ADMIN_PASSWORD` (at least 12 characters), and a long random `SECRET_KEY` in `.env` before starting the API. The first startup creates that admin account only when both admin values are explicitly configured. Rule changes and disables require the admin session and create audit-log records.

## Legal and privacy boundary

This application provides automated screening only. Production rules must be populated from verified official sources, with source references, effective dates, and rule versions. Final legal verification remains the responsibility of a competent authority or authorized professional.

Uploaded images and generated reports are local development artifacts and must be protected, retained only as needed, and excluded from version control.
