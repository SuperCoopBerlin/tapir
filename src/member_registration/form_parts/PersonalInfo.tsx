import { Form } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

type Props = {
  preferredName: string;
  setPreferredName: React.Dispatch<React.SetStateAction<string>>;
  pronouns: string;
  setPronouns: React.Dispatch<React.SetStateAction<string>>;
  dob: string;
  setDOB: React.Dispatch<React.SetStateAction<string>>;
};

export default function PersonalInfo({
  preferredName,
  setPreferredName,
  pronouns,
  setPronouns,
  dob,
  setDOB,
}: Props) {
  return (
    <>
      <Form.Group className={"mt-2"}>
        <Form.Label>
          {gettext("How would you like to be addressed? (optional)")}
        </Form.Label>
        <Form.Control
          type={"text"}
          placeholder={gettext("Your preferred name or nickname")}
          autoComplete="nickname"
          name="nickname"
          value={preferredName}
          onChange={(event) => setPreferredName(event.target.value)}
        />
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("What are your pronouns?")}</Form.Label>
        <Form.Control
          type={"text"}
          placeholder={gettext("(Optional)")}
          value={pronouns}
          name="pronouns"
          onChange={(event) => setPronouns(event.target.value)}
        />
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("What is your date of birth?")}</Form.Label>
        <Form.Control
          type={"date"}
          value={dob}
          name="dob"
          onChange={(event) => setDOB(event.target.value)}
          autoComplete="bday"
          required
        />
      </Form.Group>
    </>
  );
}
