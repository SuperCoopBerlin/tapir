# Tapir Member & Shift Management System

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Python code test coverage](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=coverage)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Lines of python code](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)

Tapir is a member and shift management system for [SuperCoop Berlin](https://supercoop.de) and [Rizoma](https://www.rizomacoop.pt/)
Our Vorstand and member office uses Tapir to manage shifts and members, for example their personal data, capabilities,
payments and shift statuses. It is also used for automatic mails and evaluate new applicants.
Members can use Tapir to register or unregister for shifts, search for a stand-in and see their shift status as well as
upcoming shifts.


<img src="https://user-images.githubusercontent.com/18083323/179391686-4cfa724f-4847-4859-aba4-f074722d69ca.png" width="68%"/> <img src="https://user-images.githubusercontent.com/18083323/179391799-96f4e204-9bd2-4739-b8f9-3bc25a70f717.JPG" width="22.6%"/>

The Tapir project is developed by SuperCoop members and is licensed under the terms of the [AGPL license](LICENSE.md).
If you're interested in using Tapir for your own coop, please contact [Théo](https://github.com/Theophile-Madet) or [SuperCoop](https://supercoop.de/en/contact/), we'll be very happy to help!

SuperCoop members can access the system at [https://members.supercoop.de](https://members.supercoop.de).

Tapir (/ˈteɪpər/) was original inspired by the french coop [L'éléfan](https://github.com/elefan-grenoble/gestion-compte), thanks to them for the inspiration.
 
A fork for community supported agriculture organization exists [here](https://github.com/FoodCoopX/wirgarten-tapir). While they stil both use the name Tapir, they have diverged a lot and don't share any code anymore.

## Getting started

### Prerequisites

- Docker
- [Poetry](https://python-poetry.org/docs/)

Please note that while the actual program runs in a Docker container, you're adviced to install packages locally in
order to use your IDE properly. For that you need a C Compiler such as gcc for Linux or the Visual C++ Build tools.

### Install

1. Clone the project.
2. Configure our pre-commit hooks: `poetry install && pre-commit install`

### Setup

Start by running:

```sh
docker compose up
```

This starts a container with an LDAP server and automatically loads the test data into the LDAP.

For local development and testing, set up the test database and load test data

```sh
# Create tables
docker compose exec web poetry run python manage.py migrate
# Copy the .env file
docker compose exec web cp .env.test .env
# Load lots of test users & shifts
docker compose exec web poetry run python manage.py generate_test_data --reset_all
```

You then can find the local instance of Tapir at [http://localhost:8000](http://localhost:8000). Login with username and
password `roberto.cortes` to get started.
For more information, have a look at our [:book: Documentation](CONTRIBUTING.md#documentation).

## Contributing

This is an active open-source project, so you can get involved in it easily!
You can do so **without any programming or Python knowledge**! Just choose a task that you like.

1. [:bug: Report issues or :bulb: suggest new features](CONTRIBUTING.md#report-issues-or-suggest-new-features)
2. [:computer: Contribute Code](CONTRIBUTING.md#contribute-code)
3. [:earth_africa: Translate Tapir](CONTRIBUTING.md#translate-tapir)
4. [:book: Improve Documentation](CONTRIBUTING.md#documentation)
5. [:apple: Become a part of SuperCoop e.G.](https://supercoop.de/en/joinus/)

## Troubleshooting

* On macOS, in order to set up a local Python `venv`, you might have to install Postgresql to get `psycopg2` working.
  Use `brew install postgresql` for that. 

## Rizoma version

Currently, two versions of Tapir exist: for SuperCoop on the `master` branch and for Rizoma under the `rizoma` branch.
If you keep the .env file as is, you'll get the SuperCoop version, which has member management and shift management.
By setting the .env file like this, you'll get the rizoma version, which concentrates on shifts and uses an external identity provider.
```dotenv
DEBUG=True
DJANGO_VITE_DEBUG=
ACTIVE_LOGIN_BACKEND=coops.pt
COOPS_PT_API_BASE_URL=https://invalid_url.com
ENABLE_RIZOMA_CONTENT=True
SHIFTS_ONLY=True
COOPS_PT_API_KEY=invalid_api_key
COOPS_PT_RSA_PUBLIC_KEY_FILE_PATH=invalid_path
TEMPLATE_SUB_FOLDER=rizoma
```

### User synchronization
Every hour, a celery task (`tapir.rizoma.tasks.sync_users_with_coops_pt_backend`) synchronizes the user list and the member list from coops.pt instance (env var `COOPS_PT_API_BASE_URL`) int the Tapir DB.
Changes done in Tapir are not reflected back to coops.pt.

Newly created users can be used to log in right away, there is no need to wait for a sync.

You can also run `manage.py sync_users_with_coops_pt_backend` to trigger a sync manually.

### Google calendar invites
When members register to a shift, it is possible to send them an invitation to a Google calendar event by mail.
This requires running local instance and the following setup:
 - get a google secret json file from your Google app (see [the docs](https://developers.google.com/workspace/calendar/api/quickstart/python))
 - on your local machine, set the env var PATH_TO_GOOGLE_CLIENT_SECRET_FILE as path to that file and start your local instance
 - run `manage.py get_google_authorized_user_file`, login if necessary and authorize the app 
 - this will create a `google_user_token.json` file
 - copy that file to your server, with the same name and relative path
 - on the feature flag page (.../core/featureflag_list), enable the relevant flag: `feature_flags.shifts.google_calendar_events_for_shifts`
 - done!