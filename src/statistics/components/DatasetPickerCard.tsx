import React, { MutableRefObject } from "react";
import { Card, Form, Table } from "react-bootstrap";
import { datasets } from "../datasets.tsx";

declare let gettext: (english_text: string) => string;

interface DatasetPickerCardProps {
  enabledDatasetsRef: MutableRefObject<Set<string>>;
  setEnabledDatasets: (set: Set<string>) => void;
}

const DatasetPickerCard: React.FC<DatasetPickerCardProps> = ({
  enabledDatasetsRef,
  setEnabledDatasets,
}) => {
  return (
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
                          enabledDatasetsRef.current.add(datasetId);
                        } else {
                          enabledDatasetsRef.current.delete(datasetId);
                        }
                        setEnabledDatasets(new Set(enabledDatasetsRef.current));
                      }}
                    />
                  </td>
                  <td>
                    <Form.Check
                      key={datasetRelativeId}
                      type={"switch"}
                      onChange={(e) => {
                        if (e.target.checked) {
                          enabledDatasetsRef.current.add(datasetRelativeId);
                        } else {
                          enabledDatasetsRef.current.delete(datasetRelativeId);
                        }
                        setEnabledDatasets(new Set(enabledDatasetsRef.current));
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
  );
};

export default DatasetPickerCard;
