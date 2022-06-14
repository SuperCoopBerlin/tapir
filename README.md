# Tapir Member & Shift Management System

Tapir is a member and shift management system to be used by [SuperCoop Berlin](https://supercoop.de).

Tapir [has a trunk](https://www.youtube.com/watch?v=JgwBecM_E6Q), but not quite such a beautiful one as 
[Mme. l'élephan](https://github.com/elefan-grenoble/gestion-compte). Tapir is badass,
[but not quite as badass as the other
animals](https://www.youtube.com/watch?v=zJm6nDnR2SE). Let's teach Tapir some tricks!

This project is licensed under the terms of the [AGPL license](LICENSE.md).
## Getting started

    docker-compose up

This starts a container with an LDAP server and automatically loads the test data into the LDAP.

Next, set up the test database and load test data

    # Create tables
    docker-compose exec web poetry run python manage.py migrate
    # Load admin (password: admin) account
    docker-compose exec web poetry run python manage.py loaddata admin_account
    # Load lots of test users & shifts
    docker-compose exec web poetry run python manage.py populate --reset_all

### Pre-existing accounts
After running the commands above, you can log-in as 3 different users. In each case, the password is the username:
 - admin (not a member, just an account with admin rights)
 - roberto.cortes (member office rights)
 - nicolas.vicente (normal member without special rights)

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

    docker-compose exec web poetry run python manage.py shell_plus

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

###  Translations
To generate the translation files, first use "makemessages" and specify the language you want to generate: 

    docker-compose exec -w /app/tapir web poetry run python ../manage.py makemessages -l de

Update tapir/translations/locale/de/LC_MESSAGES/django.po with your translations.

For the changes to take effect, restart the Docker container. This will run `manage.py compilemessages` automatically.

### How to change model classes

#### 1. Change in model class
This is quite easy by adding the property to the model class. See this page as reference:
[Python Guide - Create model in django](https://pythonguides.com/create-model-in-django/).

#### 2. Generate migration files
All changes must be done in the docker container. Since our development environment is included to the 
docker container, you must run djangos makemigrations on docker. You can do this with this command: 

    docker compose exec web poetry run python manage.py makemigrations

Please check the migration script. It might contain unwished changes. There seems to be a bug in ldpa migrations.

#### 3. Migrate development database
Last step is to update the database. this is done with this command:

    docker compose exec web poetry run python manage.py migrate

Please check, if applications runs (again).

### Welcome Desk Authentication

All users logging in at the welcome desk are granted more permissions. This magic uses SSL client certificates. The web server requests and checks the client certificate and subsequently sets a header that is then checked by `tapir.accounts.middleware.ClientPermsMiddleware`.

Here are some quick one-liners for key management:

```
# Create a new CA - only the first time. The public key in the cer file is distributed to the webserver, the private key is to be kept secret!
openssl req -newkey rsa:4096 -keyform PEM -keyout members.supercoop.de.key -x509 -days 3650 -outform PEM -nodes -out members.supercoop.de.cer -subj="/C=DE/O=SuperCoop Berlin eG/CN=members.supercoop.de"


# Create a new key
export CERT_HOSTNAME=welcome-desk-1
openssl genrsa -out $CERT_HOSTNAME.members.supercoop.de.key 4096
openssl req -new -key $CERT_HOSTNAME.members.supercoop.de.key -out $CERT_HOSTNAME.members.supercoop.de.req -sha256 -subj "/C=DE/O=SuperCoop Berlin eG/CN=welcome-desk.members.supercoop.de"
openssl x509 -req -in $CERT_HOSTNAME.members.supercoop.de.req -CA members.supercoop.de.cer -CAkey members.supercoop.de.key -CAcreateserial -extensions client -days 3650 -outform PEM -out $CERT_HOSTNAME.members.supercoop.de.cer -sha256

# Create a PKCS12 bundle consumable by the browser
openssl pkcs12 -export -inkey $CERT_HOSTNAME.members.supercoop.de.key -in $CERT_HOSTNAME.members.supercoop.de.cer -out $CERT_HOSTNAME.members.supercoop.de.p12

# Remove CSR and bundled private/public key files
rm $CERT_HOSTNAME.members.supercoop.de.key $CERT_HOSTNAME.members.supercoop.de.cer $CERT_HOSTNAME.members.supercoop.de.req
```

### Buttons
We use a slightly customized version of the boostrap buttons, typically using those HTML classes: `btn tapir-btn btn-[BOOTSTRAP COLOR]`.  
Each button should have an icon, we use material-icons.  
We use outlined buttons for links that have no consequences (for example, going to an edit page), and filled buttons when there are consequences (for example, a save button, or sending an email). 
