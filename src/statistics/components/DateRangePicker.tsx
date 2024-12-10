import React from "react";
import { FloatingLabel, Form } from "react-bootstrap";
import { getFirstOfMonth } from "../utils.tsx";

declare let gettext: (english_text: string) => string;

interface DateRangePickerProps {
  dateFrom: Date;
  setDateFrom: (date: Date) => void;
  dateTo: Date;
  setDateTo: (date: Date) => void;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
}) => {
  return (
    <>
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
        <FloatingLabel label={"Date to"}>
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
    </>
  );
};

export default DateRangePicker;
