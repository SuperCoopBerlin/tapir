import React, { useEffect, useState } from "react";
import { Card, Col, FloatingLabel, Form, Row } from "react-bootstrap";
import {
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
} from "chart.js";
import { useApi } from "../hooks/useApi.ts";
import { StatisticsApi } from "../api-client";
import { Chart } from "react-chartjs-2";

declare let gettext: (english_text: string) => string;

interface Dataset {
  apiCall: (requestParameters: { atDate: Date }, initOverrides: any) => any;
  display_name: string;
}

const FancyGraphCard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [controller, setController] = useState<AbortController>();
  const [dateFrom, setDateFrom] = useState<Date>(new Date());
  const [dateTo, setDateTo] = useState<Date>(new Date());
  const [enabledDatasets, setEnabledDatasets] = useState<Set<string>>(
    new Set(),
  );
  const api = useApi(StatisticsApi);

  const datasetNumberOfMembers = "number_of_members";
  const datasetNumberOfActiveMembers = "number_of_active_members";
  const datasets: { [key: string]: Dataset } = {
    [datasetNumberOfMembers]: {
      display_name: gettext("Number of numbers (all statuses)"),
      apiCall: api.statisticsNumberOfMembersAtDateRetrieve,
    },
    [datasetNumberOfActiveMembers]: {
      display_name: gettext(
        "Number of active numbers (active relative to the membership: paused and investing are not active, but frozen are active)",
      ),
      apiCall: api.statisticsNumberOfActiveMembersAtDateRetrieve,
    },
  };

  useEffect(() => {
    const dateFromOnPageLoad = new Date();
    dateFromOnPageLoad.setFullYear(dateFromOnPageLoad.getFullYear() - 1);
    setDateFrom(dateFromOnPageLoad);
  }, []);

  useEffect(() => {
    console.log(dateFrom);
    console.log(dateTo);
  }, [dateFrom, dateTo]);

  ChartJS.register(
    LineController,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
  );

  const data = {
    labels: ["A", "B", "C"],
    datasets: [
      {
        type: "line" as const,
        label: "Le dataset",
        data: [12, 19, 3],
        borderColor: "rgb(255, 99, 132)",
        borderWidth: 2,
        fill: false,
      },
    ],
  };

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
                    setEnabledDatasets(new Set(enabledDatasets));
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
                    setDateFrom(new Date(event.target.value));
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
                    setDateTo(new Date(event.target.value));
                  }}
                />
              </FloatingLabel>
            </Form.Group>
          </Form>
        </Col>
      </Row>
      <Row className={"mb-2"}>
        <Col>
          <div>Showing datasets: {Array.from(enabledDatasets).join(", ")}</div>
        </Col>
        <Col>
          From {dateFrom.toLocaleString()} to {dateTo.toLocaleString()}
        </Col>
      </Row>
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5>{gettext("Fancy graph")}</h5>
            </Card.Header>
            <Card.Body>
              <Chart type={"line"} data={data} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default FancyGraphCard;
