import React, { useEffect, useState } from "react";
import {
  Alert,
  Card,
  Col,
  FloatingLabel,
  Form,
  Row,
  Spinner,
  Table,
} from "react-bootstrap";
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  ChartType,
  Colors,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { useApi } from "../hooks/useApi.ts";
import { FetchError, InitOverrideFunction, StatisticsApi } from "../api-client";
import { Chart } from "react-chartjs-2";

declare let gettext: (english_text: string) => string;

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

type GraphData = {
  [datasetId: string]: (number | null)[];
};
type CachedData = {
  [datasetId: string]: { [date_as_iso_string: string]: number | null };
};

const FancyGraphCard: React.FC = () => {
  const [error, setError] = useState("");
  const [dateFrom, setDateFrom] = useState<Date>(new Date());
  const [dateTo, setDateTo] = useState<Date>(getFirstOfMonth(new Date()));
  const [enabledDatasets, setEnabledDatasets] = useState<Set<string>>(
    new Set(),
  );
  const [graphData, setGraphData] = useState<GraphData>({});
  const [graphLabels, setGraphLabels] = useState<string[]>([]);
  const [dates, setDates] = useState<Date[]>([]);
  const [fetching, setFetching] = useState(false);
  const [cachedData, setCachedData] = useState<CachedData>({});
  const api = useApi(StatisticsApi);

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

  const datasets: { [key: string]: Dataset } = {
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
        "Active in the sense of their membership: paused and investing members are not active, but frozen membersare active",
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

  useEffect(() => {
    const dateFromOnPageLoad = new Date();
    dateFromOnPageLoad.setFullYear(dateFromOnPageLoad.getFullYear() - 1);
    setDateFrom(getFirstOfMonth(dateFromOnPageLoad));
  }, []);

  useEffect(() => {
    if (!dateFrom || !dateTo) return;

    let currentDate = new Date(dateFrom);
    const dates = [];
    while (currentDate <= dateTo) {
      dates.push(currentDate);
      currentDate = new Date(currentDate);
      currentDate.setDate(currentDate.getDate() + 32);
      currentDate.setDate(1);
    }
    dates.push(currentDate);

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dates.push(tomorrow);

    setDates(dates);
    setGraphLabels(dates.map((date) => formatDate(date)));
  }, [dateFrom, dateTo]);

  function formatDate(date: Date) {
    return date.toLocaleDateString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  useEffect(() => {
    fillCachedData();
    buildAndSetGraphData();
    fetchData();
  }, [dates, enabledDatasets]);

  function fillCachedData() {
    for (const datasetId of enabledDatasets) {
      if (!Object.keys(cachedData).includes(datasetId)) {
        cachedData[datasetId] = {};
      }
      for (const date of dates) {
        if (!Object.keys(cachedData[datasetId]).includes(formatDate(date))) {
          cachedData[datasetId][formatDate(date)] = null;
        }
      }
    }
    setCachedData(cachedData);
  }

  function buildAndSetGraphData() {
    const newGraphData: GraphData = {};
    for (const datasetId of enabledDatasets) {
      newGraphData[datasetId] = dates.map(
        (date) => cachedData[datasetId][formatDate(date)],
      );
    }
    setGraphData(newGraphData);
  }

  function fetchData() {
    if (fetching) return;

    const nextDataToFetch = getNextDataToFetch();
    if (!nextDataToFetch) return;

    setError("");
    setFetching(true);

    const [datasetId, dateString] = nextDataToFetch;

    const date = new Date();
    const [day, month, year] = dateString.split(".");
    date.setDate(Number(day));
    date.setMonth(Number(month) - 1);
    date.setFullYear(Number(year));
    date.setHours(12);
    date.setMinutes(0);

    datasets[datasetId].apiCall
      .call(api, { atDate: date, relative: datasets[datasetId].relative })
      .then((value: number) => {
        cachedData[datasetId][dateString] = value;
        buildAndSetGraphData();
        setFetching(false);
        fetchData();
      })
      .catch((error: FetchError) => {
        setError("Failed to load :( error message: " + error.message);
        console.error(error);
        setFetching(false);
      });
  }

  function getNextDataToFetch() {
    for (const datasetId of enabledDatasets) {
      for (const date of Object.keys(cachedData[datasetId])) {
        if (cachedData[datasetId][date] === null) {
          return [datasetId, date];
        }
      }
    }

    return null;
  }

  ChartJS.register(
    LineController,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    Colors,
    Legend,
    Tooltip,
    BarElement,
    BarController,
  );

  const data = {
    labels: graphLabels,
    datasets: Object.entries(graphData).map(([datasetId, data]) => {
      const dataset = datasets[datasetId];
      return {
        label: dataset.display_name,
        type: dataset.chart_type,
        data: data,
        borderColor: dataset.color,
        backgroundColor: dataset.color,
        pointStyle: dataset.pointStyle,
        radius: 5,
      };
    }),
  };

  function getFirstOfMonth(date: Date) {
    date.setDate(1);
    return date;
  }

  return (
    <>
      <Row className={"mb-2"}>
        <Col>
          <Card>
            <Card.Header>
              <h5>{gettext("Pick which data to display")}</h5>
            </Card.Header>
            <Card.Body style={{ padding: "0" }}>
              <Table className={"table-striped table-hover"}>
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Color</th>
                    <th>Absolute</th>
                    <th>Relative</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(datasets).map(([datasetId, dataset]) => {
                    if (dataset.relative) {
                      return null;
                    }
                    const datasetRelativeId = datasetId + "_relative";
                    return (
                      <tr key={datasetId} style={{ verticalAlign: "middle" }}>
                        <td>{dataset.display_name}</td>
                        <td className={"fs-2"} style={{ color: dataset.color }}>
                          &#9632;
                        </td>
                        <td>
                          <Form.Check
                            type={"switch"}
                            onChange={(e) => {
                              if (e.target.checked) {
                                enabledDatasets.add(datasetId);
                              } else {
                                enabledDatasets.delete(datasetId);
                              }
                              setEnabledDatasets(new Set(enabledDatasets));
                            }}
                          />
                        </td>
                        <td>
                          <Form.Check
                            key={datasetRelativeId}
                            type={"switch"}
                            onChange={(e) => {
                              if (e.target.checked) {
                                enabledDatasets.add(datasetRelativeId);
                              } else {
                                enabledDatasets.delete(datasetRelativeId);
                              }
                              setEnabledDatasets(new Set(enabledDatasets));
                            }}
                          />
                        </td>
                        <td>
                          <div>{dataset.description}</div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className={"mb-2"}>
        <Col>
          <Card>
            <Card.Header>
              <h5>{gettext("Set date range")}</h5>
            </Card.Header>
            <Card.Body>
              <Form>
                <div className={"d-flex flex-row gap-2"}>
                  <Form.Group>
                    <FloatingLabel label={"Date from"}>
                      <Form.Control
                        type={"date"}
                        value={
                          !isNaN(dateFrom.getTime())
                            ? dateFrom.toISOString().substring(0, 10)
                            : undefined
                        }
                        onChange={(event) => {
                          setDateFrom(
                            getFirstOfMonth(new Date(event.target.value)),
                          );
                        }}
                      />
                    </FloatingLabel>
                  </Form.Group>
                  <Form.Group>
                    <FloatingLabel label={"Date from"}>
                      <Form.Control
                        type={"date"}
                        value={
                          !isNaN(dateTo.getTime())
                            ? dateTo.toISOString().substring(0, 10)
                            : undefined
                        }
                        onChange={(event) => {
                          setDateTo(
                            getFirstOfMonth(new Date(event.target.value)),
                          );
                        }}
                      />
                    </FloatingLabel>
                  </Form.Group>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      {error && (
        <Row className={"mb-2"}>
          <Col>
            <Alert variant={"danger"}>{error}</Alert>
          </Col>
        </Row>
      )}
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5>
                {gettext("Graph")} {fetching && <Spinner size={"sm"} />}
              </h5>
            </Card.Header>
            <Card.Body className={"p-2 m-2"}>
              <Chart
                type={"line"}
                data={data}
                options={{
                  scales: { y: { min: 0 } },
                  plugins: { colors: { enabled: true } },
                  animation: false,
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default FancyGraphCard;
