# Tapir Member & Shift Management System

Tapir is a member and shift management system to be used by [SuperCoop Berlin](https://supercoop.de).

Tapir [has a trunk](https://www.youtube.com/watch?v=JgwBecM_E6Q), but not quite such a beautiful one as 
[Mme. l'élephan](https://github.com/elefan-grenoble/gestion-compte). Tapir is badass,
[but not quite as badass as the other
animals](https://www.youtube.com/watch?v=zJm6nDnR2SE). Let's teach Tapir some tricks!

## Getting started

    docker-compose up

This starts a container with an LDAP server and automatically loads the test data into the LDAP.

Next, set up the test database and load test data

    # Create tables
    docker-compose exec web poetry run python manage.py migrate
    # Load admin (password: admin) account
    docker-compose exec web poetry run python manage.py loaddata accounts
    # Load lots of test users & shifts
    docker-compose exec web poetry run python manage.py populate --reset_all


## Developing

Leon uses [PyCharm](https://www.jetbrains.com/pycharm/) for development. 
It has a Poetry plugin that easily allows setting up a local (not in the container) Python env and run the tests in
there. Make sure to enable Django support in the project settings so that things like the template language and the
test runner are automagically selected (note that right now this doesn't really work anymore as the tests must be run inside docker to have an LDAP server. But PyCharm is still pretty cool)

### Pre-commit hooks

First thing after checkout, run the following to install auto-formatting using [black](https://github.com/psf/black/)
before every commit:

    poetry install && pre-commit install

### Django Shell

    docker-compose exec web poetry run python manage.py shell


### LDAP

For reading or modifying the LDAP, Apache Directory Studio is pretty handy.
    
