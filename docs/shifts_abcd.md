# An ABCD Shift

ABCD shifts represent regular shift occurrences. They contain the following information :

- A name
- A description
- A start and end time (here the time is a time-of-day, for example "15:00")
- A weekday (like Wednesday)
- A [week group](#shift-cycle--week-groups)
- A minimum number of attendances (see [Calendars](./shifts#calendars))

ABCD shifts cannot be created or edited from Tapir. Developers must create them manually.

When a single shift is generated from an ABCD shift, the single shift gets the data from the ABCD shift : name,
description, slots...

## An ABCD shift slot

An ABCD shift slot has the following information :

- A name
- [Capabilities](./shifts_single#capabilities)
- [Warnings](./shifts_single#warnings)

## ABCD shift attendances

A member can get registered to ABCD shift slots. Registration to an ABCD shift slot always happens through the member
office, normal members cannot update their own ABCD attendances in any way.

When single shifts get generated from ABCD shifts, corresponding single attendances get generated too.

Contrary to single shift attendances, ABCD shift attendances do not have a status.

## Shift cycle / Week groups

ABCD weeks are spread in 4 groups : A, B, C and D, that represent the shift cycle. Starting from the reference week (
11/04/2022), that is a week A, the following is a week B, then C, D, A, B...

All ABCD shifts are associated with a week group.