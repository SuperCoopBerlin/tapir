# Tapir — Member & Shift Management System

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Python code test coverage](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=coverage)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Lines of python code](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)

Tapir is a web application for cooperative member and shift management used by cooperatives such as [SuperCoop Berlin](https://supercoop.de) and [Rizoma](https://www.rizomacoop.pt/).
It covers member profiles, shift scheduling and booking, automatic emails, and application workflows.

<img src="https://user-images.githubusercontent.com/18083323/179391686-4cfa724f-4847-4859-aba4-f074722d69ca.png" width="68%"/> <img src="https://user-images.githubusercontent.com/18083323/179391799-96f4e204-9bd2-4739-b8f9-3bc25a70f717.JPG" width="22.6%"/>

## Key features
- **Member management:** profiles, contact details, qualifications, shopping-status, membership-fees  
- **Shift management:** create shifts, sign up, cancel, find substitutes  
- **Coop statistics:** track and vizualize purchases 
- **Mailings & notifications:** automatic emails for shifts or reminders
- **Application workflow:** review, accept or reject applicants  
- **Roles & permissions:** board, employees, member office, regular members  
- **Internationalization:** multi-language support

## Quickstart

1. Clone
```bash
git clone https://github.com/SuperCoopBerlin/tapir.git
```
2. Run `docker compose up -d`. The first time may take a while, following runs will be much shorter
3. Install migrations and generate test data:
```bash
docker compose exec web poetry run python manage.py migrate
docker compose exec web poetry run python manage.py generate_test_data --reset_all
```
Tapir should now be accessible under http://localhost:8000. You can login with username roberto.cortes and password roberto.cortes (same as the username).

## Contributing
Everyone is welcome — coding skills not required.

How to contribute
- Report issues or feature requests in Issues  
- Find beginner tasks with the `good first issue` label  
- Improve docs, translate UI strings, verify workflows, test

Developer quick steps see [CONTRIBUTING.md](CONTRIBUTING.md).

Code style & tooling
- Use `black`; pre-commit hooks recommended  
- Run `pytest` locally before PRs
- Have a look at our [wiki](https://github.com/SuperCoopBerlin/tapir/wiki) and in particular ["Setting-up-you-development-environment"](https://github.com/SuperCoopBerlin/tapir/wiki/Setting-up-you-development-environment) how to run Tapir on your machine and how to setup your IDE.

Non-technical contributions
- Translations: see [CONTRIBUTING.md](CONTRIBUTING.md) for how to add language files  
- Documentation: edit the wiki 
- Support & testing: help reproduce bugs, triage issues

## Important links
- Wiki (setup & how-tos): https://github.com/SuperCoopBerlin/tapir/wiki
- SuperCoop members can access the system at [https://members.supercoop.de](https://members.supercoop.de)
- Issues: https://github.com/SuperCoopBerlin/tapir/issues  
- Contact: If you're interested in using Tapir for your own cooperative, we'd be happy to help. Create an issue in this repo or write to [Théo](https://github.com/Theophile-Madet) directly. 


> Tapir (/ˈteɪpər/) [has a trunk](https://www.youtube.com/watch?v=JgwBecM_E6Q), but not quite such a beautiful one
> as [Mme. l'élephan](https://github.com/elefan-grenoble/gestion-compte). Tapir is
> badass, [but not quite as badass as the other animals](https://www.youtube.com/watch?v=zJm6nDnR2SE). Let's teach Tapir
> some tricks!