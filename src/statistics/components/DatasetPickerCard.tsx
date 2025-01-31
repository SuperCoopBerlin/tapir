import React, { MutableRefObject } from "react";
import { Card, Form, Spinner, Table } from "react-bootstrap";
import TapirButton from "../../components/TapirButton.tsx";
import {
  ArrowsCollapseVertical,
  ArrowsExpandVertical,
} from "react-bootstrap-icons";
import { Dataset } from "../../api-client";

declare let gettext: (english_text: string) => string;

interface DatasetPickerCardProps {
  enabledDatasetsRef: MutableRefObject<Set<Dataset>>;
  setEnabledDatasets: (set: Set<Dataset>) => void;
  enabledRelativeDatasetsRef: MutableRefObject<Set<Dataset>>;
  setEnabledRelativeDatasets: (set: Set<Dataset>) => void;
  isExpanded: boolean;
  setIsExpanded: (isExpanded: boolean) => void;
  availableDatasets: Dataset[];
  availableDatasetsLoading: boolean;
  availableDatasetsError: string;
}

const DatasetPickerCard: React.FC<DatasetPickerCardProps> = ({
  enabledDatasetsRef,
  setEnabledDatasets,
  enabledRelativeDatasetsRef,
  setEnabledRelativeDatasets,
  isExpanded,
  setIsExpanded,
  availableDatasets,
  availableDatasetsLoading,
  availableDatasetsError,
}) => {
  return (
    <Card>
      <Card.Header
        className={"d-flex justify-content-between align-items-center"}
      >
        <h5>{gettext("Pick which data to display")}</h5>
        <TapirButton
          variant={"outline-secondary"}
          icon={isExpanded ? ArrowsCollapseVertical : ArrowsExpandVertical}
          onClick={() => setIsExpanded(!isExpanded)}
        />
      </Card.Header>
      <Card.Body style={{ padding: "0" }}>
        {availableDatasetsError ? (
          <div>{availableDatasetsError}</div>
        ) : availableDatasetsLoading ? (
          <Spinner />
        ) : (
          <Table
            className={"table-striped table-hover table-bordered table-sm"}
          >
            <thead>
              <tr>
                <th>Data</th>
                <th>Color</th>
                <th>Absolute</th>
                <th>Relative</th>
                {isExpanded && <th>Description</th>}
              </tr>
            </thead>
            <tbody>
              {availableDatasets.map((dataset) => {
                return (
                  <tr key={dataset.id} style={{ verticalAlign: "middle" }}>
                    <td>{dataset.displayName}</td>
                    <td
                      className={"fs-2 text-center"}
                      style={{ color: dataset.color }}
                    >
                      &#9632;
                    </td>
                    <td className={"text-center"}>
                      <Form.Check
                        type={"switch"}
                        onChange={(e) => {
                          if (e.target.checked) {
                            enabledDatasetsRef.current.add(dataset);
                          } else {
                            enabledDatasetsRef.current.delete(dataset);
                          }
                          setEnabledDatasets(
                            new Set(enabledDatasetsRef.current),
                          );
                        }}
                      />
                    </td>
                    <td className={"text-center"}>
                      <Form.Check
                        type={"switch"}
                        onChange={(e) => {
                          if (e.target.checked) {
                            enabledRelativeDatasetsRef.current.add(dataset);
                          } else {
                            enabledRelativeDatasetsRef.current.delete(dataset);
                          }
                          setEnabledRelativeDatasets(
                            new Set(enabledRelativeDatasetsRef.current),
                          );
                        }}
                      />
                    </td>
                    {isExpanded && (
                      <td>
                        <div>{dataset.description}</div>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </Card.Body>
    </Card>
  );
};

export default DatasetPickerCard;
