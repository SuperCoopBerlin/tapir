:tada: Thanks for taking the time to contribute to Tapir! :tada:

There are many tasks to do, even without programming knowledge.
Just choose a task that you like.

1. [:bug: Report issues or :bulb: suggest new features](CONTRIBUTING.md#report-issues-or-suggest-new-features)
2. [:computer: Contribute Code](CONTRIBUTING.md#contribute-code)
3. [:earth_africa: Translate Tapir](CONTRIBUTING.md#translate-tapir)
4. [:book: Improve Documentation](CONTRIBUTING.md#documentation)
5. [:apple: Become a part of SuperCoop e.G.](https://supercoop.de/en/joinus/)

#### I just have a question?!

If you are part of SuperCoop, reach out to us on [Slack](https://supercoopberlin.slack.com/). In case you are not member
of SuperCoop, feel free to write us a mail to contact@supercoop.de.

# Report issues or suggest new features

If you have found a translation error, check [Translate Tapir](CONTRIBUTING.md#translate-tapir) to see if you can fix it
yourself.

You found a bug in Tapir? You have an idea for a neat new feature? There two possibilities to let us know:

1. Create an issue here in the repository (
   see [Github manual for how to create issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue))
2. [Contact us directly](CONTRIBUTING.md#i-just-have-a-question)

In case it is a bug, describe us how to reproduce the behaviour you've encountered and how you would expect it to be.
You can also attach screenshots, if available.

# Translate Tapir

We would be happy to have complete translations and welcome new languages!

Translations in django projects are done via translation strings in the code, which then look up the correct translation
in a message file. If no translation for the code string is available, it takes the default text (most likely in
english). Therefore, it is our responsibility to mark and translate. The system can only translate strings it knows
about.

The available translations are in
the [locale directory](https://github.com/SuperCoopBerlin/tapir/tree/master/tapir/translations). If you can't find your
language, feel free to create a new `*.po` file
and [open an issue](CONTRIBUTING.md#report-issues-or-suggest-new-features) if you need help.
Also checkout
the [django documentation for Translations](https://docs.djangoproject.com/en/4.0/topics/i18n/translation/).

# Contribute Code

If you would like to help and are able to contribute code, you are most welcome.

In this chapter, we describe the basic procedure of how you can contribute code to the repository. Make yourself
familiar with the technology stack and dependencies we use for Tapir (
see [Documentation](CONTRIBUTING.md#documentation)).

## Getting started

There are many feature requests and ideas for new features in the issue tracker which you can use. If you have own ideas
on how to improve this app and want to make sure that the pull request will be merged, it is strongly suggested you open
an issue first to discuss the feature. If you want to claim an issue for yourself, let us know by commenting the issue
with your idea how to solve it.

You can start by downloading the IDE of your choice, see our recommendations next chapter.

No code should be added the main branch directly, if you're not 100% sure about it. Instead, developers use a "
Fork-and-Branch Git Workflow" (see for
example [here](https://github.com/vicente-gonzalez-ruiz/fork_and_branch_git_workflow)).

Find instructions on how to start on our [README.md](README.md).
##### IDE

We mostly use [PyCharm](https://www.jetbrains.com/pycharm/) for development. You can fully use it for developement.
However, we are not fully happy with it since it needs the Professional License to activate full Django support
Make sure to enable Django support in the project settings so that things like the template language and the
test runner are automagically selected (note that right now this doesn't really work anymore as the tests must be run
inside docker to have an LDAP server. But PyCharm is still pretty cool).


## Style guide/code conventions

We use the `Black` package, which "can be viewed as a strict subset of PEP 8". When you installed the pre-commit
correctly as mentioned above, the style guide should be enforced automatically with every commit.

# Documentation

## Technologies used

Mostly Python with LDAP, Django but also little HTML and CSS. You can get a first idea
at [Django start](https://www.djangoproject.com/start/). For member management, we use LDAP.

The whole application is running in a docker environment, make sure it is also installed.

### Vocabulary

A few definitions to help newcomers understand the model classes.

The class name is the convention for the word in texts, followed by how to write the class in code.

| Class         | In-Code       | Definition                                                                                                                                                                                                                                                               |
|---------------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DraftUser     | `draft_user`  | Also called Applicant. Represents a person that expressed interest in joining but that hasn't completed the subscription process yet. Gets deleted when ShareOwner is created.                                                                                           |
| ShareOwner    | `share_owner` | Represents a person or a company that is either currently owning at least a share, or has owned shares in the past. Therefore they are or have been a member of the cooperative. They may not be active, for example investing members or someone who sold their shares. |
| TapirUser     | `tapir_user`  | Represents a person with a user account. Accounts are linked between Tapir and the Wiki for example. Gets created when the member becomes active (part of the shift system etc.), but can become inactive.                                                               |
| Shift         |               | Represents a shift with a specific date and time (for example, 18/06/21 10:00 to 13:00). Can be a one-time activity or an instance of a ShiftTemplate   |
| ShiftTemplate |               | Represents the recurring aspect of a shift in the ABCD system. For example helping at the shop on Tuesday, 10:00 to 13:00, on Week C. It has a weekday (Tuesday) and a time, but no date (18/06/21)    
| ShiftAttendance | 'attendances', 'shift_attendances' | Represents a state if a user register for a slot. Then a ShiftAttendance gets created, which can have several states: PENDING, DONE, CANCELLED, MISSED, MISSED_EXCUSED, LOOKING_FOR_STAND_IN. This ShiftAttendance is above all used for surverying the users obligations concerning the registered shift |

### Django Shell

```sh
docker compose exec web poetry run python manage.py shell_plus
```

### LDAP

For reading or modifying the LDAP, Apache Directory Studio is pretty handy.

### Running tests

For running the test should have a clean openldap container with the test data.

```sh
docker compose up -d openldap
```

Then, run the tests.

```sh
docker compose run --rm web poetry run pytest
```

The `--rm` option will delete the temporary containers created to run the tests. Omit it if you want to keep the
containers.

To regenerate the test data fixtures:

```sh
docker compose up --force-recreate
docker compose exec web poetry run python manage.py migrate
docker compose exec web poetry run python manage.py generate_test_data --reset_all
docker compose exec web poetry run python manage.py dumpdata accounts.TapirUser shifts.ShiftTemplateGroup shifts.ShiftTemplate shifts.ShiftSlotTemplate shifts.ShiftAttendanceTemplate coop.ShareOwner coop.ShareOwnership > tapir/utils/fixtures/test_data.json
```

#### Selenium Tests

You can connect to the selenium container via VNC for debugging purpose. The address is localhost:5900, password :
secret

### Translations

To generate the translation files, first use "makemessages" and specify the language you want to generate:

```sh
docker compose exec -w /app/tapir web poetry run python ../manage.py makemessages --no-wrap -l de
```

Update tapir/translations/locale/de/LC_MESSAGES/django.po with your translations.

For the changes to take effect, restart the Docker container. This will run `manage.py compilemessages` automatically.

You may want to use [PoEdit](https://poedit.net/) to edit the translation files.
PoEdit formats the .po file slightly differently than `makemessages` does. To keep the changes clear, run `makemessages`
again after saving from PoEdit.

### Pre-existing accounts

After running `manage.py generate_test_data --reset_all`, 400 members are created. 
You can log in as any of them, in each case, the password is the username. Here are a few examples:

- admin (not a member, just an account with admin rights)
- roberto.cortes, milla.karjala, magdalena.nieto (vorstand)
- sasha.hubert, kuzey.tahincioglu, sandra.gutierrez (member office)
- louis.robert, nicolas.vicente, mustafa.bakircioglu (normal member)

### How to change model classes

#### 1. Change in model class

This is quite easy by adding the property to the model class. See this page as reference:
[Python Guide - Create model in django](https://pythonguides.com/create-model-in-django/).

#### 2. Generate migration files

All changes must be done in the docker container. Since our development environment is included to the
docker container, you must run djangos makemigrations on docker. You can do this with this command:

```sh
docker compose exec web poetry run python manage.py makemigrations
```

Please check the migration script. It might contain unwished changes. There seems to be a bug in ldpa migrations.

#### 3. Migrate development database

Last step is to update the database. this is done with this command:

```sh
docker compose exec web poetry run python manage.py migrate
```

Please check, if applications runs (again).

### Buttons

We use a slightly customized version of the boostrap buttons, typically using those HTML
classes: `btn tapir-btn btn-[BOOTSTRAP COLOR]`.
Each button should have an icon, we use material-icons.  
We use outlined buttons for links that have no consequences (for example, going to an edit page), and filled buttons
when there are consequences (for example, a save button, or sending an email).
Use the following template tags : 
 - `{% tapir_button_link %}` for buttons that are simple links
 - `{% tapir_button_link_to_action %}` for buttons that lead to a form
 - `{% tapir_button_action %}` for actions with permanent consequences (typically, creating or saving a model)
