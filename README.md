# NUTM VITA-NOVA

**A mini Electronic Medical Records (EMR) system for the NUTM University
Clinic.**

NUTM VITA-NOVA is a role-based EMR application being developed to
support the university clinic's routine outpatient workflow. The project
aims to reduce reliance on paper-based records, improve retrieval of
patient information, and coordinate clinical activities across the
clinic's service points.

> **Development status:** This repository is an active development
> snapshot. Automated test isolation and some test-suite failures remain
> under review. The application is not represented as production-ready
> or clinically validated.

## Project objectives

-   Reduce paper-based documentation and manual record retrieval.
-   Maintain a longitudinal patient record across multiple clinic
    encounters.
-   Support coordinated workflows among front desk, nursing, medical,
    laboratory and pharmacy teams.
-   Make relevant patient and encounter information easier for
    authorised clinic personnel to retrieve.
-   Provide a foundation for further development of a university-clinic
    EMR.

## Clinic context and workflow

The system is designed around the NUTM University Clinic's routine
outpatient workflow:

1.  **Registration and records:** identify or register the patient and
    create an encounter.
2.  **Nursing:** record vital signs, anthropometric measurements and
    nursing notes.
3.  **Doctor consultation:** document the clinical assessment, diagnosis
    and management plan.
4.  **Laboratory:** receive investigation requests, process tests and
    record results.
5.  **Pharmacy:** review prescriptions and support dispensing.
6.  **Encounter continuity:** retain the encounter and clinical
    documentation within the patient's record.

The intended patient groups include students, staff and staff
dependants. The clinic context captured during requirements definition
is primarily routine outpatient care.

## Application modules

  -----------------------------------------------------------------------
  Module                              Intended responsibilities
  ----------------------------------- -----------------------------------
  Administration                      User administration and
                                      clinic-level oversight.

  Front desk                          Patient registration, patient
                                      search, profile access and
                                      encounter creation.

  Nursing                             Vital-signs capture, anthropometry
                                      and nursing documentation.

  Doctor                              Clinical consultation
                                      documentation, encounter history
                                      and review of laboratory results.

  Laboratory                          Investigation workflow and
                                      laboratory result documentation.

  Pharmacy                            Prescription review and dispensing
                                      workflow.
  -----------------------------------------------------------------------

Module availability and behaviour may change as development continues.
Refer to the application and source code for the current implementation.

## Technology

The current application uses:

-   **Python**
-   **Flask** application framework and application factory
-   **PostgreSQL** relational database
-   **SQLAlchemy** ORM
-   **Flask-Migrate** for database migrations
-   **HTML, CSS and Jinja templates** for the web interface
-   **pytest** for automated testing

## Repository structure

``` text
app/
├── admin/             # Administration routes
├── auth/              # Authentication routes
├── desk/              # Front-desk routes
├── doctor/            # Doctor workflow routes
├── laboratory/        # Laboratory routes
├── nursing/           # Nursing routes
├── pharmacy/          # Pharmacy routes
├── services/          # Application/business logic
├── static/            # CSS and image assets
└── templates/         # Jinja HTML templates
tests/                 # Automated tests
```

## Local development

### 1. Clone the repository

``` bash
git clone https://github.com/Yargamji/NUTM-VITA-NOVA.git
cd NUTM-VITA-NOVA
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

``` bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If the repository contains `requirements.txt`, install the project
dependencies with:

``` bash
pip install -r requirements.txt
```

### 4. Configure the database

Install and run PostgreSQL, create a development database, and configure
the database connection using the environment-variable names expected by
the project configuration.

The application configuration uses `DATABASE_URL`. Use a separate
database for automated tests; the test configuration uses
`TEST_DATABASE_URL`.

**Do not commit `.env` files, database passwords, API keys, patient
records or other secrets.** The repository's `.gitignore` is intended to
exclude local environment and database files.

### 5. Apply database migrations

Use the migration history included with the project to bring your
development database schema up to date. Do not point development or test
commands at a database containing real clinical records unless the
operation has been reviewed and authorised.

### 6. Run the application

``` powershell
python -m flask --app "app:create_app()" run --debug
```

The development server will print the local address in the terminal.

## Testing

The project uses `pytest`. The test suite is undergoing refactoring to
ensure that tests use a dedicated test database and isolate their data
safely.

**Current limitation:** the test suite has known failures and
test-fixture isolation issues. A clean, fully passing test run has not
yet been established. Do not run tests against a development database
containing clinical data.

When test isolation work is complete, the test instructions and verified
results will be updated here.

## Security, privacy and intended use

-   This repository is a software-development project, not a certified
    or validated clinical system.
-   Do not use it to make clinical decisions or to store real patient
    information in an unapproved environment.
-   Use synthetic data for demonstrations and development.
-   Deployments must implement appropriate authentication,
    authorisation, auditability, backup, encryption, privacy and
    operational safeguards before any real-world clinical use.
-   Never publish credentials, secrets, identifiable patient data or
    confidential institutional information.

## Roadmap

Areas for continued development include:

-   Completing test-database isolation and resolving outstanding
    automated test failures.
-   Further validating role-based access and end-to-end workflows.
-   Improving documentation and adding current application screenshots.
-   Reviewing security, privacy, audit trails, backup and deployment
    requirements.
-   Conducting appropriate user acceptance and clinical workflow
    evaluation before any operational use.

## Author and project

Developed as a health-informatics and software-development project
focused on digitising routine outpatient workflows at the NUTM
University Clinic.

**Repository:** https://github.com/Yargamji/NUTM-VITA-NOVA

------------------------------------------------------------------------

*This README describes the project's intended context and current
development snapshot. Features and implementation details may evolve.*
