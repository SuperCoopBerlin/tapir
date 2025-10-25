import { Form } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

type Props = {
  companyName: string;
  setCompanyName: React.Dispatch<React.SetStateAction<string>>;
};

export default function CompanyInfo({ companyName, setCompanyName }: Props) {
  return (
    <Form.Group className={"mt-2"}>
      <Form.Label>{gettext("What is your company name?")}</Form.Label>
      <Form.Control
        type={"text"}
        placeholder={gettext("Please enter the official company name")}
        name="companyName"
        value={companyName}
        onChange={(event) => setCompanyName(event.target.value)}
        required
      />
      <Form.Control.Feedback type="invalid">
        {gettext("Please specify the official company name.")}
      </Form.Control.Feedback>
    </Form.Group>
  );
}
