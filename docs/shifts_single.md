# Single shifts

Shifts can be created individually. The [shift creation page](https://members-test.supercoop.de/shifts/shift/create) is
accessible
from the sidebar for accounts with member office access.

Most shifts are derived from an ABCD shift. By using a dedicated command, developers can generate all shifts
corresponding to ABCD shifts up to a given date. For example, if there is an ABCD shift "Wednesdays at 12:00 on week B"
and the command is run, assuming that the week starting Monday 03/10/22 is a B week, a single shift will be created
for "Wednesday 05/10/22 at 12:00". Information are copied from the ABCD shift to the single shifts (name, description,
slots).

Single shifts are often colloquially called "flying shifts" or just "shifts". In this documentation, in order to avoid
confusion, we will try to always specify "ABCD" or "single".

A single shift has the following information:

- A name
- A description
- A start and end time (time in this case is a date and a time, example "05/10/22 at 12:00")
- A minimum number of attendances (see [Calendars](./shifts#calendars))

## Single shift slot

Even though it is often said that "a member registers to a shift", members actually register to single shift slots
instead of shifts. A shift has one or more shift slots. Each slot has the following information :

- A name
- A list of [required capabilities](#capabilities)
- A list of [warnings](#warnings)

Single shift slots can be edited or added to a shift from that shift's page.

### Capabilities

A shift slot may require capabilities. A capability represents a special training that the member must have followed
before they can work the corresponding shift slots.

A member can only register themselves to a single shift slot if they have the required capability. Accounts with member
office access can register members to slots that the members don't have the capabilities for, the page then produces a
warning that must be acknowledged.

Which capabilities a member has can be edited by accounts with member office access, use
the [edit button](https://members-test.supercoop.de/coop/member/1/edit) on the shift card for the member's page.

The list of capabilities :

- Team leader
- Cashier
- Member
- Bread delivery
- Red card
- First aid
- Welcome sessions
- Handling cheese

### Warnings

Shift slots may have one or more associated warnings. When a member registers to a shift with warnings, they must
acknowledge each warning to confirm the registration. Warnings don't restrict the registration in any other way than
this confirmation.

## Registering to single shifts

Members can freely register themselves to single shift slots, provided that :

- They have the "active" member status
- They have no active attendance for another slot of the same shift
- They have the required capabilities
- The shift is in the future
- The shift is not cancelled

Accounts with member office access can register any member to any slot. They will get a warning if the member doesn't
have the required capabilities.

For attendances that are not derived from an ABCD attendance, the member can unregister themselves up to 7 days before
the shift stats without any consequence. For ABCD attendances or within the 7 days time period, members have to look for
a [stand-in](#stand-ins).

Manual registrations to shift slots (that is, those that don't happen through the generation of single shifts from ABCD
shifts) triggers the creation of a log entry.

## Single shift attendances

Once a member registers to a shift slot, their attendance to that slot is tracked. An attendance is always in one of the
following states :

- Pending : the shift has not happened yet, the member is expected to show up normally.
- Attended : the shift has happened, the member showed up as planned.
- Cancelled : the attendance got cancelled (for example, because the shift got cancelled).
- Missed : the shift has happened and the member did not show up. They did not provide an excuse.
- Excused : the member provided an excuse for them not showing up. The slot is set free for someone else to take, but
  the excused member is otherwise considered as if they had attended the shift.
- Looking for a stand-in : see [Stand-ins](#stand-ins)

The shift page shows for each slot :

- The current "active" attendance, the member that is expected to show up
- The cancelled attendances for that slot, for example excused members or those who found a stand-in

Accounts with member office access can edit current and cancelled attendances from the shift page.

All updates to shift attendances trigger the creation of a log entry.

If an attendance is set to missed, the member that didn't show up receives an email.

## Cancelling single shifts

Accounts with member office access can cancel shifts using the dedicated button from a shift's page.

When cancelling a shift, the following happens :

- Members cannot register themselves to that shift anymore
- Members who are registered to that shift as ABCD attendance are marked as attended and their shift account is updated
  accordingly
- Members who are registered to that shift as single attendance get their attendance cancelled. Their shift account
  stays unchanged
- The shift appears greyed-out on the shift calendar

## Stand-ins

A member that cannot attend a future shift and that cannot unregister themselves from it can notify that they are
looking for a stand-in. The slot then gets highlighted with a moving icon on the shift calendar page.

Normal members can register that they are looking for a stand-in up to 2 days before the shift.

Members can register themselves to a slot currently occupied by someone that is looking for a stand-in. The attendance
of the looking member is then set as cancelled, and the attendance of the replacing member is set as pending.

When the slot is taken over, the searching member receives an email notifying that a stand-in has been found, and a log
entry gets created.

## Email reminders

Seven days before a single shift, members receive a reminder email with the date of the shift. Those emails are sent
every two hours.