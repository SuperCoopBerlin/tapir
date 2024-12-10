import React, { useEffect, useState } from "react";
import { FloatingLabel, Form } from "react-bootstrap";
import { getFirstOfMonth, getLastOfMonth } from "../utils.tsx";
import { formatDate } from "../../utils/formatDate.ts";

declare let gettext: (english_text: string) => string;

interface DateRangePickerProps {
  dateFrom: Date;
  setDateFrom: (date: Date) => void;
  dateTo: Date;
  setDateTo: (date: Date) => void;
  setDates: (dates: Date[]) => void;
  setGraphLabels: (graphLabels: string[]) => void;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  setDates,
  setGraphLabels,
}) => {
  const [includeToday, setIncludeToday] = useState(true);
  const [startOfMonth, setStartOfMonth] = useState(true);

  useEffect(() => {
    if (!dateFrom || !dateTo) return;

    let currentDate = new Date(dateFrom);
    const dates = [];
    while (currentDate <= dateTo) {
      dates.push(currentDate);
      currentDate = new Date(currentDate);
      currentDate.setDate(currentDate.getDate() + (startOfMonth ? 32 : 1));
      currentDate.setDate(1);
      currentDate = adaptDate(currentDate);
    }
    dates.push(currentDate);

    if (includeToday) {
      const today = new Date();
      let todayAlreadyInArray = false;
      for (const date of dates) {
        if (
          date.getDate() === today.getDate() &&
          date.getMonth() === today.getMonth() &&
          date.getFullYear() === today.getFullYear()
        ) {
          todayAlreadyInArray = true;
          break;
        }
      }
      if (!todayAlreadyInArray) {
        dates.push(today);
      }
    }

    dates.sort((date1, date2) => date1.getTime() - date2.getTime());

    setDates(dates);
    setGraphLabels(dates.map((date) => formatDate(date)));
  }, [dateFrom, dateTo, includeToday, startOfMonth]);

  function adaptDate(date: Date) {
    let dateAdapter = getFirstOfMonth;
    if (!startOfMonth) {
      dateAdapter = getLastOfMonth;
    }
    return dateAdapter(date);
  }

  function getDateInputValue(date: Date) {
    if (isNaN(date.getTime())) {
      return undefined;
    }
    return date.toISOString().substring(0, 10);
  }

  return (
    <>
      <Form.Group>
        <Form.Check
          type={"switch"}
          checked={includeToday}
          onChange={(e) => {
            setIncludeToday(e.target.checked);
          }}
          label={"Include today"}
        />
      </Form.Group>
      <Form.Group>
        <Form.Select
          onChange={(event) => {
            setStartOfMonth(event.target.value === "startOfMonth");
          }}
        >
          <option value={"startOfMonth"}>{gettext("First of month")}</option>
          <option value={"lastOfMonth"}>{gettext("Last of month")}</option>
        </Form.Select>
      </Form.Group>
      <Form.Group>
        <FloatingLabel label={"Date from"}>
          <Form.Control
            type={"date"}
            value={getDateInputValue(dateFrom)}
            onChange={(event) => {
              setDateFrom(adaptDate(new Date(event.target.value)));
            }}
          />
        </FloatingLabel>
      </Form.Group>
      <Form.Group>
        <FloatingLabel label={"Date to"}>
          <Form.Control
            type={"date"}
            value={getDateInputValue(dateTo)}
            onChange={(event) => {
              setDateTo(adaptDate(new Date(event.target.value)));
            }}
          />
        </FloatingLabel>
      </Form.Group>
    </>
  );
};

export default DateRangePicker;
