import React from "react";
import { Card, FloatingLabel, Form } from "react-bootstrap";
import { getFirstOfMonth } from "../utils.tsx";

declare let gettext: (english_text: string) => string;

interface DateRangePickerCardProps {
  dateFrom: Date;
  setDateFrom: (date: Date) => void;
  dateTo: Date;
  setDateTo: (date: Date) => void;
}

const DateRangePickerCard: React.FC<DateRangePickerCardProps> = ({
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
}) => {
  return (
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
                    setDateFrom(getFirstOfMonth(new Date(event.target.value)));
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
                    setDateTo(getFirstOfMonth(new Date(event.target.value)));
                  }}
                />
              </FloatingLabel>
            </Form.Group>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default DateRangePickerCard;
