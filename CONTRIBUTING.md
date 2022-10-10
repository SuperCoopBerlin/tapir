:tada: Thanks for taking the time to contribute to Tapir! :tada:

There are many tasks to do, even without programming knowledge.
Just choose a task that you like.

1. [:bug: Report issues or :bulb: suggest new features](CONTRIBUTING.md#report-issues-or-suggest-new-features)  
2. [:computer: Contribute Code](CONTRIBUTING.md#contribute-code)
3. [:earth_africa: Translate Tapir](CONTRIBUTING.md#translate-tapir)
4. [:book: Improve Documentation](CONTRIBUTING.md#documentation)
5. [:apple: Become a part of SuperCoop e.G.](https://supercoop.de/en/joinus/)


#### I just have a question?!
If you are part of SuperCoop, reach out to us on [Slack](https://supercoopberlin.slack.com/). In case you are not member of SuperCoop, feel free to write us a mail to contact@supercoop.de.

# Report issues or suggest new features
If you have found a translation error, check [Translate Tapir](CONTRIBUTING.md#translate-tapir) to see if you can fix it yourself.

You found a bug in Tapir? You have an idea for a neat new feature? There two possibilities to let us know:

1. Create an issue here in the repository (see [Github manual for how to create issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue))
2. [Contact us directly](CONTRIBUTING.md#i-just-have-a-question)

In case it is a bug, describe us how to reproduce the behaviour you've encountered and how you would expect it to be. 
You can also attach screenshots, if available.

# Translate Tapir

We would be happy to have complete translations and welcome new languages!

Translations in django projects are done via translation strings in the code, which then look up the correct translation in a message file. If no translation for the code string is available, it takes the default text (most likely in english). Therefore, it is our responsibility to mark and translate. The system can only translate strings it knows about.

The available translations are in the [locale directory](https://github.com/SuperCoopBerlin/tapir/tree/master/tapir/translations). If you can't find your language, feel free to create a new `*.po` file and [open an issue](CONTRIBUTING.md#report-issues-or-suggest-new-features) if you need help. 
Also checkout the [django documentation for Translations](https://docs.djangoproject.com/en/4.0/topics/i18n/translation/).

# Contribute Code
If you would like to help and are able to contribute code, you are most welcome.

In this chapter, we describe the basic procedure of how you can contribute code to the repository. Make yourself familiar with the technology stack and dependencies we use for Tapir (see [Documentation](CONTRIBUTING.md#documentation)).

## Getting started
There are many feature requests and ideas for new features in the issue tracker which you can use. If you have own ideas on how to improve this app and want to make sure that the pull request will be merged, it is strongly suggested you open an issue first to discuss the feature. If you want to claim an issue for yourself, let us know by commenting the issue with your idea how to solve it.

You can start by downloading the IDE of your choice, see our recommendations next chapter.

No code should be added the the main branch directly, if you're not 100% sure about it. Instead, developers use a "Fork-and-Branch Git Workflow" (see for example [here](https://github.com/vicente-gonzalez-ruiz/fork_and_branch_git_workflow)).

After cloning the project from the repository, make sure you [install the pre-commits](CONTRIBUTING.md#pre-commit-hooks).

Then start with [setting up the docker container](README.md#getting-started).

##### IDE

We mostly use [PyCharm](https://www.jetbrains.com/pycharm/) for development. You can fully use it for developement. However, we are not fully happy with it since it needs the Professional License to activate full Django support
Make sure to enable Django support in the project settings so that things like the template language and the
test runner are automagically selected (note that right now this doesn't really work anymore as the tests must be run inside docker to have an LDAP server. But PyCharm is still pretty cool).

##### Pre-commit hooks

First thing after checkout, run the following to install auto-formatting using [black](https://github.com/psf/black/): 

```
poetry install && pre-commit install
```
This will enforce certain criteria are fulfilled before every commit.

## Style guide/code conventions

We use the the `Black` package, which "can be viewed as a strict subset of PEP 8". When you installed the pre-commit correctly as mentioned above, the style guide should be enforced automatically with every commit.

# Documentation

## Technologies used

Mostly Python with LDAP, Django but also little HTML and CSS. You can get a first idea at [Django start](https://www.djangoproject.com/start/). For member management, we use LDAP.

The whole application is running in a docker environment, make sure it is also installed.

### Vocabulary

A few definitions to help newcomers understand the model classes.

The class name is the convention for the word in texts, followed by how to write the class in code.

| Class         | In-Code       | Definition                                                                                                                                                                                                                                                               |
|---------------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DraftUser     | `draft_user`  | Also called Applicant. Represents a person that expressed interest in joining but that hasn't completed the subscription process yet.                                                                                                                                    |
| Shareowner    | `share_owner` | Represents a person or a company that is either currently owning at least a share, or has owned shares in the past. Therefore they are or have been a member of the cooperative. They may not be active, for example investing members or someone who sold their shares. |
| TapirUser     | `tapir_user`  | Represents a person with a user account. Accounts are linked between Tapir and the Wiki for example. Gets created when the member becomes active (part of the shift system etc.), but can become inactive.                                                               |
| Shift         |               | Represents a shift with a specific date and time (for example, 18/06/21 10:00 to 13:00). Can be a one-time activity or an instance of a ShiftTemplate                                                                                                                    |
| ShiftTemplate |               | Represents the recurring aspect of a shift in the ABCD system. For example helping at the shop on Tuesday, 10:00 to 13:00, on Week C. It has a weekday (Tuesday) and a time, but no date (18/06/21)                                                                      |

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

### Django Shell

```
docker-compose exec web poetry run python manage.py shell_plus
```

### LDAP

For reading or modifying the LDAP, Apache Directory Studio is pretty handy.

### Running tests

For running the test should have a clean openldap container with the test data.

```
docker-compose up -d openldap
```

Then, run the tests.

```
docker-compose run --rm web poetry run pytest
```
The `--rm` option will delete the temporary containers created to run the tests. Omit it if you want to keep the containers.

To regenerate the test data fixtures:

```
docker-compose up --force-recreate
docker compose exec web poetry run python manage.py migrate
docker compose exec web poetry run python manage.py generate_test_data --reset_all
docker-compose exec web poetry run python manage.py dumpdata accounts.TapirUser shifts.ShiftTemplateGroup shifts.ShiftTemplate shifts.ShiftSlotTemplate shifts.ShiftAttendanceTemplate coop.ShareOwner coop.ShareOwnership > tapir/utils/fixtures/test_data.json
```

#### Selenium Tests

You can connect to the selenium container via VNC for debugging purpose. The address is localhost:5900, password : secret

### Translations

To generate the translation files, first use "makemessages" and specify the language you want to generate:

```
docker-compose exec -w /app/tapir web poetry run python ../manage.py makemessages -l de
```

Update tapir/translations/locale/de/LC_MESSAGES/django.po with your translations.

For the changes to take effect, restart the Docker container. This will run `manage.py compilemessages` automatically.

You may want to use [PoEdit](https://poedit.net/) to edit the translation files.
PoEdit formats the .po file slightly differently than `makemessages` does. To keep the changes clear, run `makemessages` again after saving from PoEdit.

### Pre-existing accounts

After running the commands above, you can log-in as 3 different users. In each case, the password is the username:

- admin (not a member, just an account with admin rights)
- roberto.cortes (member office rights)
- nicolas.vicente (normal member without special rights)

### How to change model classes

#### 1. Change in model class

This is quite easy by adding the property to the model class. See this page as reference:
[Python Guide - Create model in django](https://pythonguides.com/create-model-in-django/).

#### 2. Generate migration files

All changes must be done in the docker container. Since our development environment is included to the 
docker container, you must run djangos makemigrations on docker. You can do this with this command:

```
docker compose exec web poetry run python manage.py makemigrations
```

Please check the migration script. It might contain unwished changes. There seems to be a bug in ldpa migrations.

#### 3. Migrate development database

Last step is to update the database. this is done with this command:

```
docker compose exec web poetry run python manage.py migrate
```

Please check, if applications runs (again).

### Buttons

We use a slightly customized version of the boostrap buttons, typically using those HTML classes: `btn tapir-btn btn-[BOOTSTRAP COLOR]`.  
Each button should have an icon, we use material-icons.  
We use outlined buttons for links that have no consequences (for example, going to an edit page), and filled buttons when there are consequences (for example, a save button, or sending an email).
