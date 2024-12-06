import React, { MutableRefObject } from "react";
import { Card, Form, Table } from "react-bootstrap";
import { datasets } from "../datasets.tsx";
import TapirButton from "../../components/TapirButton.tsx";
import {
  ArrowsCollapseVertical,
  ArrowsExpandVertical,
} from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

interface DatasetPickerCardProps {
  enabledDatasetsRef: MutableRefObject<Set<string>>;
  setEnabledDatasets: (set: Set<string>) => void;
  isExpanded: boolean;
  setIsExpanded: (isExpanded: boolean) => void;
}

const DatasetPickerCard: React.FC<DatasetPickerCardProps> = ({
  enabledDatasetsRef,
  setEnabledDatasets,
  isExpanded,
  setIsExpanded,
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
        <Table className={"table-striped table-hover table-bordered table-sm"}>
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
            {Object.entries(datasets).map(([datasetId, dataset]) => {
              if (dataset.relative) {
                return null;
              }
              const datasetRelativeId = datasetId + "_relative";
              return (
                <tr key={datasetId} style={{ verticalAlign: "middle" }}>
                  <td>{dataset.display_name}</td>
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
                          enabledDatasetsRef.current.add(datasetId);
                        } else {
                          enabledDatasetsRef.current.delete(datasetId);
                        }
                        setEnabledDatasets(new Set(enabledDatasetsRef.current));
                      }}
                    />
                  </td>
                  <td className={"text-center"}>
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
      </Card.Body>
    </Card>
  );
};

export default DatasetPickerCard;
