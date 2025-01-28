import {InitOverrideFunction, StatisticsApi} from "../api-client";
import {ChartType} from "chart.js";
import {useApi} from "../hooks/useApi.ts";

declare let gettext: (english_text: string) => string;

const datasetNumberOfMembers = "number_of_members";
const datasetNumberOfActiveMembers = "number_of_active_members";
const datasetNumberOfActiveMembersWithAccount = "number_of_active_members_with_account";
const datasetNumberOfInvestingMembers = "number_of_investing_members";
const datasetNumberOfPausedMembers = "number_of_paused_members";
const datasetNumberOfWorkingMembers = "number_of_working_members";
const datasetNumberOfPurchasingMembers = "number_of_purchasing_members";
const datasetNumberOfFrozenMembers = "number_of_frozen_members";
const datasetNumberOfLongTermFrozenMembers =
  "number_of_long_term_frozen_members";
const datasetNumberOfShiftPartners = "number_of_shift_partners";
const datasetNumberOfCoPurchasers = "number_of_co_purchasers";
const datasetNumberOfFlyingMembers = "number_of_flying_members";
const datasetNumberOfAbcdMembers = "number_of_abcd_members";
const datasetNumberOfPendingResignations = "number_of_pending_resignations";
const datasetNumberOfCreatedResignations = "number_of_created_resignations";
const datasetNumberOfExemptedMembers = "number_of_exempted_members";
const datasetNumberOfExemptedMembersThatWork =
  "number_of_exempted_members_that_work";

// Colors from https://mokole.com/palette.html
// or https://lospec.com/palette-list/syz15

// Point styles from https://www.chartjs.org/docs/latest/configuration/elements.html#info

interface Dataset {
  apiCall: (
    requestParameters: { atDate: Date; relative: boolean },
    initOverrides?: RequestInit | InitOverrideFunction,
  ) => any;
  display_name: string;
  description?: string;
  chart_type: ChartType;
  relative: boolean;
  color: string;
  pointStyle: string;
}

const api = useApi(StatisticsApi);

export const datasets: { [key: string]: Dataset } = {
  [datasetNumberOfMembers]: {
    display_name: gettext("Total members"),
    description: gettext(
      "Ignoring status: investing and paused members are included",
    ),
    apiCall: api.statisticsNumberOfMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#0e0c19",
    pointStyle: "circle",
  },
  [datasetNumberOfActiveMembers]: {
    display_name: gettext("Active members"),
    description: gettext(
      "Active in the sense of their membership: paused and investing members are not active, but frozen members are active",
    ),
    apiCall: api.statisticsNumberOfActiveMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#9d1f2f",
    pointStyle: "cross",
  },
  [datasetNumberOfActiveMembersWithAccount]: {
    display_name: gettext("Active members with Tapir account"),
    description: gettext(
      "Same as active members, but also had an account at the given date. Some members declare themselves active when joining the coop but never come to activate their account.",
    ),
    apiCall: api.statisticsNumberOfActiveMembersWithAccountAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#bd3f4f",
    pointStyle: "circle",
  },
  [datasetNumberOfInvestingMembers]: {
    display_name: gettext("Investing members"),
    apiCall: api.statisticsNumberOfInvestingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#f28c8c",
    pointStyle: "crossRot",
  },
  [datasetNumberOfPausedMembers]: {
    display_name: gettext("Paused members"),
    apiCall: api.statisticsNumberOfPausedMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#b05621",
    pointStyle: "dash",
  },
  [datasetNumberOfWorkingMembers]: {
    display_name: gettext("Working members"),
    apiCall: api.statisticsNumberOfWorkingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#c9ad23",
    pointStyle: "line",
  },
  [datasetNumberOfPurchasingMembers]: {
    display_name: gettext("Purchasing members"),
    description: gettext(
      "Members who are allowed to shop. To be allowed to shop, a member must be active (see the description for \"Active members\"), have a Tapir account, and not be frozen.",
    ),
    apiCall: api.statisticsNumberOfPurchasingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#d8e1a9",
    pointStyle: "rect",
  },
  [datasetNumberOfFrozenMembers]: {
    display_name: gettext("Frozen members"),
    description: gettext(
      "Counted out of 'active' members: paused and investing members not counted.",
    ),
    apiCall: api.statisticsNumberOfFrozenMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#52b466",
    pointStyle: "rectRounded",
  },
  [datasetNumberOfLongTermFrozenMembers]: {
    display_name: gettext("Long-term frozen members"),
    description: gettext(
      "Members that are frozen since more than 180 days (roughly 6 month). Long-term frozen members are included in the \"Frozen members\" dataset",
    ),
    apiCall: api.statisticsNumberOfLongTermFrozenMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#0e4f38",
    pointStyle: "rectRot",
  },
  [datasetNumberOfShiftPartners]: {
    display_name: gettext("Shift partners"),
    description: gettext(
      "Counted out of working members only: a frozen member with a shift partner is not counted",
    ),
    apiCall: api.statisticsNumberOfShiftPartnersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#68062f",
    pointStyle: "star",
  },
  [datasetNumberOfCoPurchasers]: {
    display_name: gettext("Co-purchasers"),
    description: gettext(
      "Only members who can shop are counted: members that have a co-purchaser but are not allowed to shop are not counted",
    ),
    apiCall: api.statisticsNumberOfCoPurchasersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#8d5a88",
    pointStyle: "triangle",
  },
  [datasetNumberOfFlyingMembers]: {
    display_name: gettext("Flying members"),
    description: gettext(
      "Only members who work are counted: members that are exempted, paused, frozen... are not counted",
    ),
    apiCall: api.statisticsNumberOfFlyingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#126f7e",
    pointStyle: "circle",
  },
  [datasetNumberOfAbcdMembers]: {
    display_name: gettext("ABCD members"),
    description: gettext(
      "Only members who work are counted: members that are exempted, paused, frozen... are not counted",
    ),
    apiCall: api.statisticsNumberOfAbcdMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#53269a",
    pointStyle: "cross",
  },
  [datasetNumberOfPendingResignations]: {
    display_name: gettext("Pending resignations"),
    description: gettext(
      "Members who want to get their money back and are waiting for the 3 year term",
    ),
    apiCall: api.statisticsNumberOfPendingResignationsAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#221452",
    pointStyle: "crossRot",
  },
  [datasetNumberOfCreatedResignations]: {
    display_name: gettext("Created resignations"),
    description: gettext(
      "Regardless of whether the member gifts their share or get their money back, this is relative to when the resignation is created.",
    ),
    apiCall: api.statisticsNumberOfCreatedResignationsInSameMonthRetrieve,
    chart_type: "line",
    relative: false,
    color: "#122f70",
    pointStyle: "dash",
  },
  [datasetNumberOfExemptedMembers]: {
    display_name: gettext("Exempted members"),
    description: gettext(
      "Counting only members that would work if they were not exempted: frozen and investing members with an exemption are not counted. ",
    ),
    apiCall: api.statisticsNumberOfExemptedMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#223421",
    pointStyle: "dash",
  },
  [datasetNumberOfExemptedMembersThatWork]: {
    display_name: gettext("Exempted members that work"),
    description: gettext(
      "Counting all exempted members (ignoring if they are frozen or investing) that actually did a shift in the past 60 days. Just registering to the shift doesn't count, the attendance must be confirmed. ",
    ),
    apiCall: api.statisticsNumberOfExemptedMembersThatWorkRetrieve,
    chart_type: "line",
    relative: false,
    color: "#cc33cc",
    pointStyle: "dash",
  },
};

for (const [datasetId, dataset] of Object.entries(datasets)) {
  datasets[datasetId + "_relative"] = {
    display_name: dataset.display_name + " (relative)",
    apiCall: dataset.apiCall,
    chart_type: "bar",
    relative: true,
    color: dataset.color,
    pointStyle: dataset.pointStyle,
  };
}
