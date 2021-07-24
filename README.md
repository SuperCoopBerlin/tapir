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

### Running tests

For running the test should have a clean openldap container with the test data.

    docker-compose up -d openldap

Then, run the tests.

    docker-compose run web poetry run pytest

To regenerate the test data fixtures:

    docker-compose up --force-recreate
    docker compose exec web poetry run python manage.py migrate
    docker compose exec web poetry run python manage.py populate --reset_all
    docker-compose exec web poetry run python manage.py dumpdata accounts.TapirUser shifts.ShiftTemplateGroup shifts.ShiftTemplate shifts.ShiftSlotTemplate shifts.ShiftAttendanceTemplate coop.ShareOwner coop.ShareOwnership > tapir/utils/fixtures/test_data.json

#### Selenium Tests
You can connect to the selenium container via VNC for debugging purpose. The address is localhost:5900, password : secret
 
### Vocabulary
A few definitions to help newcomers understand the model classes. 

| Class | Definition |
| ----- | ---------- |
| DraftUser | Also called Applicant. Represents a person that expressed interest in joining but that hasn't completed the subscription process yet. |
| ShareOwner | Represents a person or a company that is either currently owning at least a share, or has owned shares in the past. Therefore they are or have been a member of the cooperative. They may not be active, for example investing members or someone who sold their shares. |
| TapirUser | Represents a person with a user account. Accounts are linked between Tapir and the Wiki for example. Gets created when the member becomes active (part of the shift system etc.), but can become inactive. |  
| Shift | Represents a shift with a specific date and time (for example, 18/06/21 10:00 to 13:00). Can be a one-time activity or an instance of a ShiftTemplate |
| ShiftTemplate | Represents the recurring aspect of a shift in the ABCD system. For example helping at the shop on Tuesday, 10:00 to 13:00, on Week C. It has a weekday (Tuesday) and a time, but no date (18/06/21) | 
