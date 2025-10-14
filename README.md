# Tapir Member & Shift Management System

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Python code test coverage](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=coverage)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)
[![Lines of python code](https://sonarcloud.io/api/project_badges/measure?project=SuperCoopBerlin_tapir&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=SuperCoopBerlin_tapir)

Tapir is a member and shift management system of the cooperatives [SuperCoop Berlin](https://supercoop.de) and [Rizoma](https://www.rizomacoop.pt/).
Our Vorstand and member office uses Tapir to manage shifts and members, for example their personal data, capabilities,
payments and shift statuses. It is also used for automatic mails and evaluate new applicants.
Members can use Tapir to register or unregister for shifts, search for a stand-in and see their shift status as well as
upcoming shifts.

<img src="https://user-images.githubusercontent.com/18083323/179391686-4cfa724f-4847-4859-aba4-f074722d69ca.png" width="68%"/> <img src="https://user-images.githubusercontent.com/18083323/179391799-96f4e204-9bd2-4739-b8f9-3bc25a70f717.JPG" width="22.6%"/>

The Tapir project is developed by SuperCoop members with contributions from Rizoma. It is licensed under the terms of the [AGPL license](LICENSE.md).

SuperCoop members can access the system at [https://members.supercoop.de](https://members.supercoop.de).

If you're interested in using Tapir for your own cooperative, we'd be happy to help. Contact us by creating an issue in this repo or write [Théo](https://github.com/Theophile-Madet) directly.

> Tapir (/ˈteɪpər/) [has a trunk](https://www.youtube.com/watch?v=JgwBecM_E6Q), but not quite such a beautiful one
> as [Mme. l'élephan](https://github.com/elefan-grenoble/gestion-compte). Tapir is
> badass, [but not quite as badass as the other animals](https://www.youtube.com/watch?v=zJm6nDnR2SE). Let's teach Tapir
> some tricks!

## Getting started
We have a [wiki](https://github.com/SuperCoopBerlin/tapir/wiki) on GitHub. In particular, check [this page](https://github.com/SuperCoopBerlin/tapir/wiki/Setting-up-you-development-environment) to run Tapir on your machine and how to setup your IDE.

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
