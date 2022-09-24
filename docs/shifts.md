# Shifts

Shifts represent work that members can provide for the organisation. Each shift has one or more slots that member can
register to, thus committing to doing the corresponding work at the given time.

## ABCD shifts and single shifts

There are two types of shifts : ABCD and single.

A single shift represents a specific moment. It is associated with a specific date and time. Example : 24/09/2022 at 15:
00).

An ABCD shift represents a regular occurrence : It is associated with a weekday, a time in the day, and a week group.
Example : Each Wednesday of weeks B, at 12:00.

- [Single shifts](./shifts_single)
- [ABCD shifts](./shifts_abcd)

## Attendance types

There are two attendance types :

- ABCD, for members that are expected to register to one ABCD shift
- Flying, for members that never register to ABCD shifts but instead register to single shifts.

The attendance type is only informative, it does not influence shift registration or attendance logic.

## Shift accounts

The shift account system helps track attendances. Members are supposed to attend one shift per cycle.

Automatically at the beginning of each cycle, 1 point is removed from each member who is supposed to do a shift this
cycle. Members are expected to do shifts if :

- Their member status is active
- Their account got created before the shift cycle started
- They are not [exempted](#shift-exemptions) at the beginning of the cycle

Three things can influence the account balance of a member :

- When they were registered to a shift slot, and their attendance got confirmed, they get +1
- When they were registered to a shift, and they get marked as no-show, they get -2
- Accounts with member office access can create arbitrary entries with any value to the shift account

### Members on alert

There is a list of [members on alert](https://members-test.supercoop.de/shifts/members_on_alert) showing all members
that have an account balance of -2 or less.

The [welcome desk](./welcome_desk) shows members with a balance of -2 or less as on alert.

## Shift exemptions

Members can get exempted for doing shifts.
The [list of exemptions](https://members-test.supercoop.de/shifts/shift_exemption) is accessible from the sidebar.
Exempted users don't get -1 on their shift accounts on cyle starts.

An exemption can be created by going to the list of exemptions for that member (accessible from that member's profile
page), then clicking the create button on the top right.

An exemption has the following information :

- Start date
- End date (optional, the exemption is infinite if no end date is set)
- Description

When creating or editing an exemption, shift attendances can get cancelled :

- Single attendances within the timeframe of the exemption get cancelled, whether they are derived from ABCD attendances
  or not.
- If the exemption is longer than 6 cycles, the member gets unregistered from all their ABCD shifts. All future single
  attendances derived from those ABCD attendances get cancelled, even those that are outside the timeframe of the
  exemption.

## Calendars

There are four calendars available : past single shifts, future single shifts, ABCD shifts, ABCD groups.

Single and ABCD shift calendars, by default, highlight the shifts that have fewer people registered to them than
required. There are also filters to highlight shifts that have a free slot for a particular slot name.

[Single shift calendars](https://members.supercoop.de/shifts/calendar) show single shifts grouped by date. For each
date, there is a button to download the attendance list for all the shifts of that day, in a printable format.

The [ABCD shift calendar](https://members.supercoop.de/shifts/shifttemplate/overview) shows the ABCD shifts grouped by
weekday and week group.

## Statistics

There is a dedicated page for shift statistics. The following statistics are available :

- Ratio of flying members to ABCD members,
- Ratio of members that are expected to do shifts against total members
- Ratio of number of ABCD slots relative to the number of members expected to do shifts
- Number of slots for each slot type
- Evolution of the number of members doing shifts