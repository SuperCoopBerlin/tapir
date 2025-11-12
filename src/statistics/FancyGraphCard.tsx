import React, { MutableRefObject, useEffect, useRef, useState } from "react";
import { Alert, Card, Col, Row, Spinner } from "react-bootstrap";
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
import { Dataset, FetchError, StatisticsApi } from "../api-client";
import { Chart } from "react-chartjs-2";
import { formatDate } from "../utils/formatDate.ts";
import DatasetPickerCard from "./components/DatasetPickerCard.tsx";
import { getFirstOfMonth } from "./utils.tsx";
import TapirButton from "../components/TapirButton.tsx";
import { Download } from "react-bootstrap-icons";
import DateRangePicker from "./components/DateRangePicker.tsx";
import ColourblindnessTypePicker from "./components/ColourblindnessTypePicker.tsx";

declare let gettext: (english_text: string) => string;

type GraphData = {
  [datasetId: string]: (number | null)[];
};
type CachedData = {
  [datasetId: string]: { [date_as_iso_string: string]: number | null };
};

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

const FancyGraphCard: React.FC = () => {
  const [error, setError] = useState("");
  const [dateFrom, setDateFrom] = useState<Date>(new Date());
  const [dateTo, setDateTo] = useState<Date>(getFirstOfMonth(new Date()));
  const [enabledNotRelativeDatasets, setEnabledNotRelativeDatasets] = useState<
    Set<Dataset>
  >(new Set<Dataset>());
  const enabledDatasetsNotRelativeRef = useRef<Set<Dataset>>(
    new Set<Dataset>(),
  );
  const [enabledRelativeDatasets, setEnabledRelativeDatasets] = useState<
    Set<Dataset>
  >(new Set<Dataset>());
  const enabledRelativeDatasetsRef = useRef<Set<Dataset>>(new Set<Dataset>());
  const [graphData, setGraphData] = useState<GraphData>({});
  const [graphLabels, setGraphLabels] = useState<string[]>([]);
  const [dates, setDates] = useState<Date[]>([]);
  const [fetching, setFetching] = useState(false);
  const [datapickerExpanded, setDatapickerExpanded] = useState(false);
  const cachedDataNotRelative = useRef<CachedData>({});
  const cachedDataRelative = useRef<CachedData>({});
  const api = useApi(StatisticsApi);
  const [availableDatasetsLoading, setAvailableDatasetsLoading] =
    useState(false);
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([]);
  const [availableDatasetsError, setAvailableDatasetsError] = useState("");
  const [selectedColourblindnessType, setSelectedColourblindnessType] =
    useState("");

  useEffect(() => {
    setAvailableDatasetsLoading(true);

    api
      .statisticsAvailableDatasetsList({
        colourblindness: selectedColourblindnessType,
      })
      .then(setAvailableDatasets)
      .catch(setAvailableDatasetsError)
      .finally(() => setAvailableDatasetsLoading(false));
  }, [selectedColourblindnessType]);

  useEffect(() => {
    const dateFromOnPageLoad = new Date();
    dateFromOnPageLoad.setFullYear(dateFromOnPageLoad.getFullYear() - 1);
    setDateFrom(getFirstOfMonth(dateFromOnPageLoad));
  }, []);

  useEffect(() => {
    fillCachedData(enabledDatasetsNotRelativeRef, cachedDataNotRelative);
    fillCachedData(enabledRelativeDatasetsRef, cachedDataRelative);
    buildAndSetGraphData();
    fetchData();
  }, [dates, enabledNotRelativeDatasets, enabledRelativeDatasets]);

  function fillCachedData(
    datasetsRef: MutableRefObject<Set<Dataset>>,
    cachedDataRef: MutableRefObject<CachedData>,
  ) {
    for (const dataset of datasetsRef.current) {
      if (!Object.keys(cachedDataRef.current).includes(dataset.id)) {
        cachedDataRef.current[dataset.id] = {};
      }
      for (const date of dates) {
        if (
          !Object.keys(cachedDataRef.current[dataset.id]).includes(
            formatDate(date),
          )
        ) {
          cachedDataRef.current[dataset.id][formatDate(date)] = null;
        }
      }
    }
  }

  function buildAndSetGraphData() {
    const newGraphData: GraphData = {};
    for (const dataset of enabledDatasetsNotRelativeRef.current) {
      newGraphData[dataset.id] = dates.map(
        (date) => cachedDataNotRelative.current[dataset.id][formatDate(date)],
      );
    }
    for (const dataset of enabledRelativeDatasetsRef.current) {
      newGraphData[dataset.id + "_relative"] = dates.map(
        (date) => cachedDataRelative.current[dataset.id][formatDate(date)],
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

    const [datasetId, dateString, relative] = nextDataToFetch;

    const date = new Date();
    const [day, month, year] = dateString.split(".");
    date.setFullYear(Number(year));
    date.setMonth(Number(month) - 1);
    date.setDate(Number(day));
    date.setHours(12);
    date.setMinutes(0);

    api
      .statisticsGraphPointRetrieve({
        atDate: date,
        relative: relative,
        dataset: datasetId,
      })
      .then((value: number) => {
        (relative ? cachedDataRelative : cachedDataNotRelative).current[
          datasetId
        ][dateString] = value;
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

  function getNextDataToFetch(): [string, string, boolean] | null {
    for (const dataset of enabledDatasetsNotRelativeRef.current) {
      for (const date of Object.keys(
        cachedDataNotRelative.current[dataset.id],
      )) {
        if (cachedDataNotRelative.current[dataset.id][date] === null) {
          return [dataset.id, date, false];
        }
      }
    }

    for (const dataset of enabledRelativeDatasetsRef.current) {
      for (const date of Object.keys(cachedDataRelative.current[dataset.id])) {
        if (cachedDataRelative.current[dataset.id][date] === null) {
          return [dataset.id, date, true];
        }
      }
    }

    return null;
  }

  const data = {
    labels: graphLabels,
    datasets: Object.entries(graphData).map(([datasetId, data]) => {
      const dataset = availableDatasets.find(
        (dataset) => dataset.id === datasetId.replace("_relative", ""),
      );
      return {
        label: dataset!.displayName,
        type: (datasetId.endsWith("_relative") ? "bar" : "line") as ChartType,
        data: data,
        borderColor: dataset!.color,
        backgroundColor: dataset!.color,
        pointStyle: dataset!.pointStyle,
        radius: 5,
      };
    }),
  };

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

  function getCurrentDataAsCsvString() {
    let string = "date";
    for (const datasetId of Object.keys(graphData)) {
      string += "," + datasetId;
    }
    string += "\n";

    for (const [index, date] of dates.entries()) {
      string += formatDate(date);

      for (const datasetValues of Object.values(graphData)) {
        string += "," + datasetValues[index];
      }
      string += "\n";
    }

    return string;
  }

  function downloadCurrentData() {
    const element = document.createElement("a");
    element.setAttribute(
      "href",
      "data:text/plain;charset=utf-8," +
        encodeURIComponent(getCurrentDataAsCsvString()),
    );
    const filename =
      "tapir graph export " + formatDate(new Date(), true) + ".csv";
    element.setAttribute("download", filename);

    element.style.display = "none";
    element.click();
  }

  return (
    <>
      {error && (
        <Row className={"mb-2"}>
          <Col>
            <Alert variant={"danger"}>{error}</Alert>
          </Col>
        </Row>
      )}
      <Row>
        <Col className={"mb-2 " + (datapickerExpanded ? "" : "col-xxl-3")}>
          <DatasetPickerCard
            setEnabledDatasets={setEnabledNotRelativeDatasets}
            enabledDatasetsRef={enabledDatasetsNotRelativeRef}
            setEnabledRelativeDatasets={setEnabledRelativeDatasets}
            enabledRelativeDatasetsRef={enabledRelativeDatasetsRef}
            isExpanded={datapickerExpanded}
            setIsExpanded={setDatapickerExpanded}
            availableDatasets={availableDatasets}
            availableDatasetsError={availableDatasetsError}
            availableDatasetsLoading={availableDatasetsLoading}
          />
        </Col>
        <Col>
          <Card>
            <Card.Header
              className={"d-flex align-items-center justify-content-between"}
            >
              <h5>
                {gettext("Graph")} {fetching && <Spinner size={"sm"} />}
              </h5>
              <span className={"d-flex gap-2 align-items-center"}>
                <DateRangePicker
                  dateFrom={dateFrom}
                  setDateFrom={setDateFrom}
                  dateTo={dateTo}
                  setDateTo={setDateTo}
                  setDates={setDates}
                  setGraphLabels={setGraphLabels}
                />
                <ColourblindnessTypePicker
                  setSelectedColourblindnessType={
                    setSelectedColourblindnessType
                  }
                />
                <TapirButton
                  variant={"outline-secondary"}
                  text={"Download as CSV"}
                  icon={Download}
                  onClick={downloadCurrentData}
                />
              </span>
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
