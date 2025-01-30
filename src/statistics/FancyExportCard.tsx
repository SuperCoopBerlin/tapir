import React, { useEffect, useState } from "react";
import {
  Card,
  Col,
  FloatingLabel,
  Form,
  Row,
  Spinner,
  Table,
} from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { DatapointExport, StatisticsApi } from "../api-client";
import { getDateInputValue } from "./utils.tsx";
import TapirButton from "../components/TapirButton.tsx";
import { Download } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const FancyExportCard: React.FC = () => {
  const api = useApi(StatisticsApi);
  const [error, setError] = useState("");
  const [availableColumns, setAvailableColumns] = useState<string[]>([]);
  const [availableColumnsLoading, setAvailableColumnsLoading] = useState(false);
  const [enabledColumns, setEnabledColumns] = useState<Set<string>>(
    new Set<string>(),
  );
  const [date, setDate] = useState<Date>(new Date());
  const [rows, setRows] = useState<DatapointExport[]>([]);

  useEffect(() => {
    setAvailableColumnsLoading(true);
    api
      .statisticsAvailableExportColumnsViewList()
      .then((columns) => {
        setAvailableColumns(columns.map((column) => column.columnName));
      })
      .catch(setError)
      .finally(() => {
        setAvailableColumnsLoading(false);
      });
  }, []);

  function buildColumnCheckboxes() {
    return (
      <ul>
        {availableColumns.map((columnName) => (
          <Form.Check
            key={columnName}
            type={"switch"}
            label={columnName}
            onChange={(e) => {
              const newEnabledColumnsSet = new Set(enabledColumns);
              if (e.target.checked) {
                newEnabledColumnsSet.add(columnName);
              } else {
                newEnabledColumnsSet.delete(columnName);
              }
              setEnabledColumns(newEnabledColumnsSet);
            }}
          />
        ))}
      </ul>
    );
  }

  function doDownload() {
    api
      .statisticsAbcdMemberExportViewList({
        exportColumns: Array.from(enabledColumns),
        atDate: date,
      })
      .then((rows) => {
        setRows(rows);
      });
  }

  function snakeCaseToCamelCase(input: string): string {
    return input
      .split("_")
      .reduce(
        (output, word, i) =>
          i === 0
            ? word.toLowerCase()
            : `${output}${word.charAt(0).toUpperCase()}${word
                .substring(1)
                .toLowerCase()}`,
        "",
      );
  }

  return (
    <>
      <Row>
        <Col>
          <Card>
            <Card.Header
              className={"d-flex align-items-center justify-content-between"}
            >
              <h5>{gettext("Fancy export")}</h5>
            </Card.Header>
            <Card.Body className={"p-2 m-2"}>
              <div>
                {error ? (
                  <div>{error}</div>
                ) : availableColumnsLoading ? (
                  <Spinner />
                ) : (
                  <ul>{buildColumnCheckboxes()}</ul>
                )}
              </div>
              <div>
                <Form.Group>
                  <FloatingLabel label={"Date"}>
                    <Form.Control
                      type={"date"}
                      value={getDateInputValue(date)}
                      onChange={(event) => {
                        setDate(new Date(event.target.value));
                      }}
                    />
                  </FloatingLabel>
                </Form.Group>
              </div>
              <div>
                <TapirButton
                  variant={"outline-secondary"}
                  text={"Download active members"}
                  icon={Download}
                  onClick={() => {
                    doDownload();
                  }}
                />
              </div>
              <div>
                <Table
                  className={
                    "table-striped table-hover table-bordered table-sm"
                  }
                >
                  <thead>
                    <tr>
                      {Array.from(enabledColumns).map((columnName) => (
                        <th key={columnName}>{columnName}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, index) => (
                      <tr key={index}>
                        {Array.from(enabledColumns).map((columnName) => (
                          <td key={index.toString() + "_" + columnName}>
                            {
                              row[
                                snakeCaseToCamelCase(
                                  columnName,
                                ) as keyof DatapointExport
                              ]
                            }
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default FancyExportCard;
