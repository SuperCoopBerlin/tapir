import { Form } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

type Props = {
  isCompany: boolean | null;
  setIsCompany: React.Dispatch<React.SetStateAction<boolean | null>>;
  setIsInvesting: React.Dispatch<React.SetStateAction<boolean>>;
};

export default function JoiningAs({ isCompany, setIsCompany }: Props) {
  return (
    <Form.Group className={"mt-3 mb-3"}>
      <h6 className="mt-4 mb-3">
        {gettext("Are you joining as an individual or company?")}
      </h6>
      <Form.Check
        type={"radio"}
        id="joining-as-individual"
        label={gettext("Individual")}
        checked={isCompany === false}
        name="joiningAs"
        onChange={(event) => {
          setIsCompany(!event.target.checked);
        }}
        required
      />
      <Form.Check
        type={"radio"}
        id="joining-as-company"
        label={gettext("Company")}
        checked={isCompany === true}
        name="joiningAs"
        onChange={(event) => {
          setIsCompany(event.target.checked);
          setIsInvesting(event.target.checked);
        }}
        required
      />
    </Form.Group>
  );
}
