# Tapir Member & Shift Management System

Tapir is a member and shift management system of the food cooperative [SuperCoop Berlin](https://supercoop.de).
Our Vorstand and member office uses Tapir to manage shifts and members, for example their personal data, capabilities,
payments and shift statuses. It is also used for automatic mails and evaluate new applicants.
Members can use Tapir to register or unregister for shifts, search for a stand-in and see their shift status as well as
upcoming shifts.

<img src="https://user-images.githubusercontent.com/18083323/179391686-4cfa724f-4847-4859-aba4-f074722d69ca.png" width="68%"/> <img src="https://user-images.githubusercontent.com/18083323/179391799-96f4e204-9bd2-4739-b8f9-3bc25a70f717.JPG" width="22.6%"/>

The Tapir project is developed by SuperCoop members, in collaberation with [WirMarkt Hamburg](https://wirmarkt.de/) and
is licensed under the terms of the [AGPL license](LICENSE.md).

SuperCoop members can access the system at [https://members.supercoop.de](https://members.supercoop.de).

> Tapir (/ˈteɪpər/) [has a trunk](https://www.youtube.com/watch?v=JgwBecM_E6Q), but not quite such a beautiful one
> as [Mme. l'élephan](https://github.com/elefan-grenoble/gestion-compte). Tapir is
> badass, [but not quite as badass as the other animals](https://www.youtube.com/watch?v=zJm6nDnR2SE). Let's teach Tapir
> some tricks!

## Getting started

1. Clone the project
2. install docker
3. configure our [pre-commit hooks](CONTRIBUTING.md#pre-commit-hooks)

Then you can start by running

```
docker compose up
```

This starts a container with an LDAP server and automatically loads the test data into the LDAP.

For local development and testing, set up the test database and load test data

```
# Create tables
docker-compose exec web poetry run python manage.py migrate
# Load admin (password: admin) account
docker-compose exec web poetry run python manage.py loaddata admin_account
# Load lots of test users & shifts
docker-compose exec web poetry run python manage.py generate_test_data --reset_all
```

You then can find the local instance of Tapir at [http://localhost:8000](http://localhost:8000). Login with username and
password `roberto.cortes` to get started.
For more information, have a look at our [Documentation](CONTRIBUTING.md#documentation).

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
