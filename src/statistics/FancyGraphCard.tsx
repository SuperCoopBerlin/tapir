import React, { useEffect, useState } from "react";
import {
  Alert,
  Card,
  Col,
  FloatingLabel,
  Form,
  Row,
  Spinner,
} from "react-bootstrap";
import {
  CategoryScale,
  Chart as ChartJS,
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
import { Line } from "react-chartjs-2";

declare let gettext: (english_text: string) => string;

interface Dataset {
  apiCall: (
    requestParameters: { atDate: Date },
    initOverrides?: RequestInit | InitOverrideFunction,
  ) => any;
  display_name: string;
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
  const datasetNumberOfCoPurchasers = "number_of_cp_purchasers";
  const datasetNumberOfFlyingMembers = "number_of_flying_members";
  const datasetNumberOfAbcdMembers = "number_of_abcd_members";

  const datasets: { [key: string]: Dataset } = {
    [datasetNumberOfMembers]: {
      display_name: gettext("Number of numbers (all statuses)"),
      apiCall: api.statisticsNumberOfMembersAtDateRetrieve,
    },
    [datasetNumberOfActiveMembers]: {
      display_name: gettext(
        "Number of active members (active relative to the membership: paused and investing are not active, but frozen are active)",
      ),
      apiCall: api.statisticsNumberOfActiveMembersAtDateRetrieve,
    },
    [datasetNumberOfInvestingMembers]: {
      display_name: gettext("Number of investing members"),
      apiCall: api.statisticsNumberOfInvestingMembersAtDateRetrieve,
    },
    [datasetNumberOfPausedMembers]: {
      display_name: gettext("Number of paused members"),
      apiCall: api.statisticsNumberOfPausedMembersAtDateRetrieve,
    },
    [datasetNumberOfWorkingMembers]: {
      display_name: gettext("Number of working members"),
      apiCall: api.statisticsNumberOfWorkingMembersAtDateRetrieve,
    },
    [datasetNumberOfPurchasingMembers]: {
      display_name: gettext("Number of purchasing members"),
      apiCall: api.statisticsNumberOfPurchasingMembersAtDateRetrieve,
    },
    [datasetNumberOfFrozenMembers]: {
      display_name: gettext("Number of frozen members"),
      apiCall: api.statisticsNumberOfFrozenMembersAtDateRetrieve,
    },
    [datasetNumberOfLongTermFrozenMembers]: {
      display_name: gettext("Number of long term frozen members"),
      apiCall: api.statisticsNumberOfLongTermFrozenMembersAtDateRetrieve,
    },
    [datasetNumberOfShiftPartners]: {
      display_name: gettext("Number of shift partners"),
      apiCall: api.statisticsNumberOfShiftPartnersAtDateRetrieve,
    },
    [datasetNumberOfCoPurchasers]: {
      display_name: gettext(
        "Number of co-purchasers (out of the members who can shop, frozen & co not counted)",
      ),
      apiCall: api.statisticsNumberOfCoPurchasersAtDateRetrieve,
    },
    [datasetNumberOfFlyingMembers]: {
      display_name: gettext(
        "Number of flying members (out of the members who work, exempted, paused and co not counted)",
      ),
      apiCall: api.statisticsNumberOfFlyingMembersAtDateRetrieve,
    },
    [datasetNumberOfAbcdMembers]: {
      display_name: gettext(
        "Number of abcd members (out of the members who work, exempted, paused and co not counted)",
      ),
      apiCall: api.statisticsNumberOfAbcdMembersAtDateRetrieve,
    },
  };

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
      .call(api, { atDate: date })
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
  );

  const data = {
    labels: graphLabels,
    datasets: Object.entries(graphData).map(([datasetId, data]) => {
      return {
        label: datasets[datasetId].display_name,
        data: data,
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
          {Object.entries(datasets).map(([datasetId, dataset]) => {
            return (
              <Form.Check
                key={datasetId}
                type={"switch"}
                label={dataset.display_name}
                onChange={(e) => {
                  if (e.target.checked) {
                    enabledDatasets.add(datasetId);
                  } else {
                    enabledDatasets.delete(datasetId);
                  }
                  setEnabledDatasets(new Set(enabledDatasets));
                }}
              />
            );
          })}
        </Col>
        <Col>
          <Form>
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
                    setDateFrom(getFirstOfMonth(new Date(event.target.value)));
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
                    setDateTo(getFirstOfMonth(new Date(event.target.value)));
                  }}
                />
              </FloatingLabel>
            </Form.Group>
          </Form>
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
                {gettext("Fancy graph")} {fetching && <Spinner size={"sm"} />}
              </h5>
            </Card.Header>
            <Card.Body className={"p-2 m-2"}>
              <Line
                data={data}
                options={{
                  scales: { y: { min: 0 } },
                  plugins: { colors: { enabled: true, forceOverride: true } },
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
