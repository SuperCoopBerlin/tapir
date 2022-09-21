# Tapir feature documentation

This is the feature documentation for Tapir.

Tapir is a member management tool targeted at cooperatives.
It helps members and organisers keep track of membership statuses.

This documentation aims to be :

- Exhaustive : it should describe everything that Tapir does.
- Readable by anyone : it is not targeted at developers
- Not specific to a particular organisation : while this is the Tapir version used by SuperCoop Berlin, this document
  intends to describe what Tapir does rather than how SuperCoop works.

When referring to a specific page, the links lead to the test instance of Tapir for SuperCoop Berlin. This instance
contains only fake information (therefore no private information) and can be edited without consequence.

## Members

Tapir keeps track of past, present and future members.
The [list of members](https://members-test.supercoop.de/coop/member/) can be accessed with the "Members" link of the
sidebar.

### A member

The following information are stored for each member.

- Their unique member number
- First name
- Last name
- Email-Address
- Phone number
- Date of birth
- Address (street, house number, postcode, city, country)
- Language (EN or DE)
- Whether they attended a welcome session or not

Normal members can see information about themselves.
Members with member-office access can see and edit the information of all members.

### Creating a member

The first step to create a member is to create an Applicant. This can be done with the create button on the top right of
the [Applicant list page](https://members-test.supercoop.de/coop/user/draft/).

#### Applicants

Applicants can be created with partial information. They are intended to store whatever information is available about a
person that expressed interest in joining the organization.

All the information stored about members can also be saved on applicants. All the fields can be edited from the
applicant's page.
On top of those are also saved :

- Whether the person has signed a membership agreement yet
- How many shares they would like to buy.

The membership agreement can be downloaded as PDF from the applicant's page, prefilled with the available information.

It is possible to delete on applicant from the applicant's page.

#### From Applicant to member

A member can be created from an applicant from the applicant's page if the following conditions are met :

- The applicant has a first name, last name, email-address
- The membership agreement has been signed
- The applicant intends to buy at least one share.

Creating a member from an applicant :

- Deletes the applicant
- Creates the member
- Creates the desired number of shares for that member, with the current day's date as starting validity for the shares
- Sends a membership confirmation email to the new member, with a membership confirmation PDF attached. Active members
  and investing members receive a different email.

Creating a member on Tapir does not automatically create a Tapir account for them. See the member account documentation.

### Member status

Tapir recognized three statuses for members :

- Active : for most members
- Investing : for members who don't take part in the organisation's activity. This can restrict what they
  are able to do within the organisation. For example at SuperCoop Berlin, they don't do any shift, but are not allowed
  to vote or shop.
- Sold : for people who had shares but sold them (either to other members or back to the organisation). They are not
  members of the organisation anymore.

### Filters

The [member list page](https://members-test.supercoop.de/coop/member/) offers several filters. Filters can be combined
freely. The following filters are available :
- Has participated in a welcome session
- Is paying by installments
- Is a company
- Membership status
- Shift status
- Is registered to a shift that requires a specific capability
- Has a specific shift capability
- Has a tapir account
- Is registered to an ABCD shift on a specific week
- Has completed payments
- Name or member number

#### Exporting the list

The filtered list of members can be downloaded as a CSV or JSON file using the buttons at the top right of the member
list page. The fields included in the export are :

- First name
- Last name
- Street and house number
- Post code
- City
- Country
- Membership status
- Participation to a welcome session
- Paying my installments
- Is a company
- Email-Address
- Phone number
- Company name
- Language
- Number of shares
- When they became a member

## Shares

Each member can own shares of the organisation.

A share has a start date and an optional end date.
The start date is usually the date at which the member is created.
The end date is used for two cases :

- When a share is transferred from a member to another. In that case, the share of the giving member gets the transfer
  date as end date. A new share gets created for the receiving member, with the transfer date as start date.
- When a member sells their share back to the organisation.

A share without an end date is considered valid forever.

### Creating more shares

A member can buy more shares from the organisation. This can be done from the member's page by clicking the "Add shares"
button. That button is visible after clicking "details" next to the user's number of shares.

Creating more shares will send a confirmation email to the member, with a confirmation PDF attached.

### Accounting recap

At midnight every sunday (in the night from Saturday to Sunday), an email gets sent to the accounting email address. In
the email is the list of all new members with the amount of shares they got created with, and the list of extra shares
that got bought by existing members. For each of those entry, the email contains a link to download the PDF
confirmation.

### Matching program

Members can register to the "Matching Program" to signify that they are willing to pay for the share of a potential new
member that could not afford it themselves.

The date of the registration is stored, so that the members who are the longest in the program get asked first about
gifting opportunities.

When "gifting" a share, the gifting member actually never gets the share added to their account. Instead, the share gets
created on the receiving member's account, but the payment is registered with the gifting member as "paying member" and
the receiving member as "credited member". See the payment document.

## Member accounts

Members don't automatically get an account on Tapir. The account gets created with a manual step after creating the
member, by clicking the "Create Tapir account" button on the member's page. The button is only visible for member's that
don't already have an account.

Examples of members who don't need an account :

- Companies
- Investing members

Upon creating an account, an email gets sent to the corresponding member, containing their username and a link to set
their password.

The username for the created account gets set on creation and **can not** be changed later.

### Logging in

Members can log in with their username or password. If they forgot one or the other, they can ask for a password reset
link to be sent by email. Their username is included in the email.

Logged-in users can change their passwords from their password page.

If a member forgot their username, password and email-address, they can contact the member office. People with member
office access can re-send the account activation link from the member's page, that will include the username and a
password reset link.

## Payments

While Tapir does not aim to be a full-fledge accounting software, it allows tracking of payments from members to the
organisation. This allows members to see how far they are in their payments, and organisers to get a list of members who
haven't completed their payments yet.

A payment can be created from the [payment list page](https://members-test.supercoop.de/coop/payments/list). It contains
the following information :

- The paying member
- The credited member. In most cases, it is the same as the paying member, but can be different in case a member gifts a
  share to another member. See _Matching Program_
- The amount paid
- The date at which the payment happened
- An optional comment
- The date at which the payment is created in Tapir is saved and set automatically.
- The account that created the payment

The member's page show how much a member is expected to pay and how much they paid until now. The expected payment is
calculated with the following formula. Shares that are past their end date are still included.

```
number_of_shares * price_of_a_share + entry_fee
```

The [member list page](https://members-test.supercoop.de/coop/member/) has a filter to show only members that have not
completed their payments.

Editing payments is not possible after creation. Only developers can edit payments.

The [payment list page](https://members-test.supercoop.de/coop/payments/list) has the following filter :

- By payment date
- By payment creation date in Tapir
- By paying member
- By credited member
- By creating member (the person who registered the payment in Tapir)

Normal members can see only see payments that they are involved in as paying or credited member. The names of the other
involved people are anonymize. Accounts with member office access can see all payments with complete information.

### Access rights

## Logs

## Shifts

### ABCD and flying

### Welcome desk

Mitkäufer

### A shift

#### A shift slot

### Shift capabilities

### Shift accounts

### Shift exemptions

## Emails

## Financing campains

## Statistics