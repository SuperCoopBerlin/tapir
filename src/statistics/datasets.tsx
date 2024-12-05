import { InitOverrideFunction, StatisticsApi } from "../api-client";
import { ChartType } from "chart.js";
import { useApi } from "../hooks/useApi.ts";

declare let gettext: (english_text: string) => string;

const datasetNumberOfMembers = "number_of_members";
const datasetNumberOfActiveMembers = "number_of_active_members";
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

// Colors from https://mokole.com/palette.html
// or https://lospec.com/palette-list/simple-14

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
    color: "#000000",
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
    color: "#e3dac9",
    pointStyle: "cross",
  },
  [datasetNumberOfInvestingMembers]: {
    display_name: gettext("Investing members"),
    apiCall: api.statisticsNumberOfInvestingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#318ce7",
    pointStyle: "crossRot",
  },
  [datasetNumberOfPausedMembers]: {
    display_name: gettext("Paused members"),
    apiCall: api.statisticsNumberOfPausedMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#0b486b",
    pointStyle: "dash",
  },
  [datasetNumberOfWorkingMembers]: {
    display_name: gettext("Working members"),
    apiCall: api.statisticsNumberOfWorkingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#272941",
    pointStyle: "line",
  },
  [datasetNumberOfPurchasingMembers]: {
    display_name: gettext("Purchasing members"),
    apiCall: api.statisticsNumberOfPurchasingMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#1cceb7",
    pointStyle: "rect",
  },
  [datasetNumberOfFrozenMembers]: {
    display_name: gettext("Frozen members"),
    apiCall: api.statisticsNumberOfFrozenMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#008080",
    pointStyle: "rectRounded",
  },
  [datasetNumberOfLongTermFrozenMembers]: {
    display_name: gettext("Long-term frozen members"),
    apiCall: api.statisticsNumberOfLongTermFrozenMembersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#1b4d3e",
    pointStyle: "rectRot",
  },
  [datasetNumberOfShiftPartners]: {
    display_name: gettext("Shift partners"),
    apiCall: api.statisticsNumberOfShiftPartnersAtDateRetrieve,
    chart_type: "line",
    relative: false,
    color: "#2c9c38",
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
    color: "#f0a830",
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
    color: "#ffa4e9",
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
    color: "#e95081",
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
    color: "#7b1e7a",
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
    color: "#841b2d",
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
