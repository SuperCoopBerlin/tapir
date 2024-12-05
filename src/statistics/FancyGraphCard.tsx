import React, { useEffect, useRef, useState } from "react";
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
  BarController,
  BarElement,
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
import { FetchError, StatisticsApi } from "../api-client";
import { Chart } from "react-chartjs-2";
import { datasets } from "./datasets.tsx";
import { formatDate } from "../utils/formatDate.ts";
import DatasetPickerCard from "./components/DatasetPickerCard.tsx";

declare let gettext: (english_text: string) => string;

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
    new Set<string>(),
  );
  const enabledDatasetsRef = useRef<Set<string>>(new Set<string>());
  const [graphData, setGraphData] = useState<GraphData>({});
  const [graphLabels, setGraphLabels] = useState<string[]>([]);
  const [dates, setDates] = useState<Date[]>([]);
  const [fetching, setFetching] = useState(false);
  const cachedData = useRef<CachedData>({});
  const api = useApi(StatisticsApi);

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

  useEffect(() => {
    fillCachedData();
    buildAndSetGraphData();
    fetchData();
  }, [dates, enabledDatasets]);

  function fillCachedData() {
    for (const datasetId of enabledDatasetsRef.current) {
      if (!Object.keys(cachedData.current).includes(datasetId)) {
        cachedData.current[datasetId] = {};
      }
      for (const date of dates) {
        if (
          !Object.keys(cachedData.current[datasetId]).includes(formatDate(date))
        ) {
          cachedData.current[datasetId][formatDate(date)] = null;
        }
      }
    }
  }

  function buildAndSetGraphData() {
    const newGraphData: GraphData = {};
    for (const datasetId of enabledDatasetsRef.current) {
      newGraphData[datasetId] = dates.map(
        (date) => cachedData.current[datasetId][formatDate(date)],
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
        cachedData.current[datasetId][dateString] = value;
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
    for (const datasetId of enabledDatasetsRef.current) {
      for (const date of Object.keys(cachedData.current[datasetId])) {
        if (cachedData.current[datasetId][date] === null) {
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

  function getYScaleMinimum() {
    let min = 0;
    for (const values of Object.values(graphData)) {
      for (const value of values) {
        if (value === null) continue;
        min = Math.min(min, value);
      }
    }
    return min;
  }

  return (
    <>
      <Row className={"mb-2"}>
        <Col>
          <DatasetPickerCard
            setEnabledDatasets={setEnabledDatasets}
            enabledDatasetsRef={enabledDatasetsRef}
          />
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
                  scales: { y: { min: getYScaleMinimum() } },
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
