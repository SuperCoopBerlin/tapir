import React, { useEffect, useState } from "react";
import { useApi } from "../../hooks/useApi.ts";
import { StatisticsApi } from "../../api-client";
import { FloatingLabel, Form } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

interface ColourblindnessTypePickerProps {
  setSelectedColourblindnessType: (colourblindnessType: string) => void;
}

const ColourblindnessTypePicker: React.FC<ColourblindnessTypePickerProps> = ({
  setSelectedColourblindnessType,
}) => {
  const api = useApi(StatisticsApi);
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);

  useEffect(() => {
    api
      .statisticsAvailableColourblindnessTypesRetrieve()
      .then(setAvailableTypes);
  }, []);

  return (
    <Form.Group className={"mb-1"}>
      <FloatingLabel label={"Pick a colourblindness"}>
        <Form.Select
          onChange={(event) => {
            setSelectedColourblindnessType(event.target.value);
          }}
        >
          <option value={""}>{gettext("No colourblindness")}</option>
          {availableTypes.map((type) => (
            <option value={type} key={type}>
              {type}
            </option>
          ))}
        </Form.Select>
      </FloatingLabel>
    </Form.Group>
  );
};

export default ColourblindnessTypePicker;
