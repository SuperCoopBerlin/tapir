import React, { useEffect, useState } from "react";
import { Badge, Card, Col, Form, Row, Spinner, Table } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { DatapointExport, Dataset, StatisticsApi } from "../api-client";
import { getDateInputValue } from "./utils.tsx";
import TapirButton from "../components/TapirButton.tsx";
import { Copy, Download } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const FancyExportCard: React.FC = () => {
  const api = useApi(StatisticsApi);
  const [availableColumnsError, setAvailableColumnsError] = useState("");
  const [availableColumns, setAvailableColumns] = useState<string[]>([]);
  const [availableColumnsLoading, setAvailableColumnsLoading] = useState(false);
  const [date, setDate] = useState<Date>(new Date());
  const [rows, setRows] = useState<DatapointExport[]>([]);
  const [availableDatasetsError, setAvailableDatasetsError] = useState("");
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([]);
  const [availableDatasetsLoading, setAvailableDatasetsLoading] =
    useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | undefined>();
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(
    new Set<string>(),
  );
  const [exportDownloading, setExportDownloading] = useState(false);
  const [downloadExportError, setDownloadExportError] = useState("");

  useEffect(() => {
    setAvailableColumnsLoading(true);
    api
      .statisticsAvailableExportColumnsList()
      .then((columns) => {
        setAvailableColumns(columns.map((column) => column.columnName));
      })
      .catch(setAvailableColumnsError)
      .finally(() => {
        setAvailableColumnsLoading(false);
      });
  }, []);

  useEffect(() => {
    setAvailableDatasetsLoading(true);

    api
      .statisticsAvailableDatasetsList({ colourblindness: "" })
      .then(setAvailableDatasets)
      .catch(setAvailableDatasetsError)
      .finally(() => {
        setAvailableDatasetsLoading(false);
      });
  }, []);

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

  function addExportColumnToSelection(columnName: string) {
    const newSelectedColumnsSet = new Set(selectedColumns);
    newSelectedColumnsSet.add(columnName);
    setSelectedColumns(newSelectedColumnsSet);
    setRows([]);
  }

  function removeExportColumnFromSelection(columnName: string) {
    const newSelectedColumnsSet = new Set(selectedColumns);
    newSelectedColumnsSet.delete(columnName);
    setSelectedColumns(newSelectedColumnsSet);
    setRows([]);
  }

  function downloadExport() {
    if (!selectedDataset) {
      alert("You must first select which dataset you want to export");
      return;
    }

    setExportDownloading(true);
    api
      .statisticsExportDatasetList({
        exportColumns: Array.from(selectedColumns),
        dataset: selectedDataset.id,
        atDate: date,
      })
      .then(setRows)
      .catch(setDownloadExportError)
      .finally(() => setExportDownloading(false));
  }

  function copyExportToClipboard() {
    let text = Array.from(selectedColumns).join(",");
    text += "\n" + rows.map((row) => buildRowExport(row)).join("\n");
    navigator.clipboard.writeText(text).then(() => {
      alert("Copied");
    });
  }

  function buildRowExport(row: DatapointExport): string {
    return Array.from(selectedColumns)
      .map((columnName) =>
        buildColumnExport(
          row[snakeCaseToCamelCase(columnName) as keyof DatapointExport],
        ),
      )
      .join(",");
  }

  function buildColumnExport(
    columnValue: string | number | boolean | string[] | undefined,
  ): string {
    if (typeof columnValue === "boolean") {
      return columnValue ? "True" : "False";
    }

    if (Array.isArray(columnValue)) {
      return columnValue.join(" - ");
    }

    return columnValue ? columnValue.toString() : "N/A";
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
              <div className={"d-flex flex-column gap-2"}>
                <div className={"d-flex flex-row gap-2"}>
                  {availableDatasetsError ? (
                    <div>{availableDatasetsError}</div>
                  ) : availableDatasetsLoading ? (
                    <Spinner />
                  ) : (
                    <Form.Group
                      style={{ flexBasis: 0, flexGrow: 1 }}
                      controlId={"sourceDataset"}
                    >
                      <Form.Label>{gettext("Source dataset")}</Form.Label>
                      <Form.Select
                        onChange={(event) => {
                          for (const dataset of availableDatasets) {
                            if (dataset.id == event.target.value) {
                              setSelectedDataset(dataset);
                              setRows([]);
                              return;
                            }
                          }
                          setSelectedDataset(undefined);
                        }}
                      >
                        <option value={""}></option>
                        {availableDatasets.map((dataset) => (
                          <option value={dataset.id} key={dataset.id}>
                            {dataset.displayName}
                          </option>
                        ))}
                      </Form.Select>
                      {selectedDataset && (
                        <Form.Text>{selectedDataset.description}</Form.Text>
                      )}
                    </Form.Group>
                  )}
                  <Form.Group style={{ flexBasis: 0, flexGrow: 1 }}>
                    <Form.Label>{gettext("Date")}</Form.Label>
                    <Form.Control
                      type={"date"}
                      value={getDateInputValue(date)}
                      onChange={(event) => {
                        setDate(new Date(event.target.value));
                      }}
                    />
                    <Form.Text>
                      {gettext(
                        "The date is only relevant for the following fields: shift_status, is_working, is_exempted, is_paused, can_shop. " +
                          "For all other fields, the value as it is now is exported, not the value as it was at the given date.",
                      )}
                    </Form.Text>
                  </Form.Group>
                </div>
                <div>
                  {availableColumnsError ? (
                    <div>{availableColumnsError}</div>
                  ) : availableColumnsLoading ? (
                    <Spinner />
                  ) : (
                    <Form.Group>
                      <Form.Label>
                        {gettext("Add columns to the export")}
                      </Form.Label>
                      <Form.Select
                        onChange={(event) => {
                          addExportColumnToSelection(event.target.value);
                        }}
                      >
                        <option value=""></option>
                        {availableColumns
                          .filter((column) => !selectedColumns.has(column))
                          .map((column) => (
                            <option value={column} key={column}>
                              {column}
                            </option>
                          ))}
                      </Form.Select>
                      <Form.Text>
                        {gettext("Click on a selected column to deselect it.")}
                      </Form.Text>
                    </Form.Group>
                  )}
                </div>
                <div className={"d-flex flex-row gap-2"}>
                  {Array.from(selectedColumns).map((column) => (
                    <Badge
                      onClick={() => removeExportColumnFromSelection(column)}
                      style={{ cursor: "pointer" }}
                      key={column}
                    >
                      {column}
                    </Badge>
                  ))}
                </div>
                <div className={"d-flex flex-row gap-2"}>
                  <TapirButton
                    variant={"outline-secondary"}
                    text={
                      selectedDataset
                        ? gettext("Build export for ") +
                          selectedDataset.displayName
                        : gettext("Pick a source dataset")
                    }
                    icon={Download}
                    onClick={() => {
                      downloadExport();
                    }}
                    disabled={!selectedDataset}
                    loading={exportDownloading}
                  />
                  <TapirButton
                    variant={"outline-secondary"}
                    text={
                      rows.length > 0
                        ? gettext("Copy export to clipboard")
                        : gettext("Build the export to copy it")
                    }
                    icon={Copy}
                    onClick={() => {
                      copyExportToClipboard();
                    }}
                    disabled={rows.length === 0}
                  />
                </div>
                <div>
                  {downloadExportError ? (
                    downloadExportError
                  ) : rows.length === 0 ? (
                    <div>{gettext("Waiting for build")}</div>
                  ) : (
                    <Table
                      className={
                        "table-striped table-hover table-bordered table-sm"
                      }
                    >
                      <thead>
                        <tr>
                          {Array.from(selectedColumns).map((columnName) => (
                            <th key={columnName}>{columnName}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row, index) => (
                          <tr key={index}>
                            {Array.from(selectedColumns).map((columnName) => (
                              <td key={index.toString() + "_" + columnName}>
                                {buildColumnExport(
                                  row[
                                    snakeCaseToCamelCase(
                                      columnName,
                                    ) as keyof DatapointExport
                                  ],
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default FancyExportCard;
