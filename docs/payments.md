# Payments

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