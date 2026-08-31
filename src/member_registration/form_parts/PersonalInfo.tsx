import { useMemo } from "react";
import { Form } from "react-bootstrap";
import { MIN_REGISTRATION_AGE, PreferredLanguage } from "../constants";

declare let gettext: (english_text: string) => string;

type Props = {
  preferredName: string;
  setPreferredName: React.Dispatch<React.SetStateAction<string>>;
  pronouns: string;
  setPronouns: React.Dispatch<React.SetStateAction<string>>;
  dob: string;
  setDOB: React.Dispatch<React.SetStateAction<string>>;
  preferredLanguage: PreferredLanguage;
  setPreferredLanguage: React.Dispatch<React.SetStateAction<PreferredLanguage>>;
  isInvesting: boolean;
};

export default function PersonalInfo({
  preferredName,
  setPreferredName,
  pronouns,
  setPronouns,
  dob,
  setDOB,
  preferredLanguage,
  setPreferredLanguage,
  isInvesting,
}: Props) {
  const dobMax = useMemo(() => {
    const max = new Date();
    max.setFullYear(max.getFullYear() - MIN_REGISTRATION_AGE);

    const yyyy = max.getFullYear().toString().padStart(4, "0");
    const mm = max.getMonth().toString().padStart(2, "0");
    const dd = max.getDay().toString().padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }, []);

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
        <Form.Text>
          {gettext(`This field is optional. If you give a preferred name, your administrative name will only
                    be shown on your profile and administrative documents, which are visible only by you and the organization's admins. Your
                    preferred name will be used everywhere else (on the shift's timetable, at the welcome
                    desk...)`)}
        </Form.Text>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("What are your pronouns? (optional)")}</Form.Label>
        <Form.Control
          type={"text"}
          placeholder={gettext("Pronouns")}
          value={pronouns}
          name="pronouns"
          autoComplete="off"
          onChange={(event) => setPronouns(event.target.value)}
        />
        <Form.Text>
          {gettext("Pronouns will be shown for example on shift timetables.")}
        </Form.Text>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("What is your date of birth?")}</Form.Label>
        <Form.Control
          type={"date"}
          value={dob}
          name="dob"
          onChange={(event) => setDOB(event.target.value)}
          autoComplete="bday"
          max={dobMax}
          style={{ width: "auto" }}
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext(
            "Please specify your date of birth. You must be 18 years or older to become a member.",
          )}
        </Form.Control.Feedback>
      </Form.Group>
      {!isInvesting && (
        <Form.Group className={"mt-2"}>
          <Form.Label>
            {gettext("Which language do you want to use for Tapir?")}
          </Form.Label>
          <Form.Select
            value={preferredLanguage}
            name="preferredLanguage"
            onChange={(event) =>
              setPreferredLanguage(event.target.value as PreferredLanguage)
            }
            style={{ width: "auto" }}
            required
          >
            <option value={PreferredLanguage.GERMAN}>🇩🇪 Deutsch</option>
            <option value={PreferredLanguage.ENGLISH}>🇬🇧 English</option>
          </Form.Select>
          <Form.Text>
            Tapir is our member and shift management system. You will use it to
            register for your shifts.
          </Form.Text>
          <Form.Control.Feedback type="invalid">
            {gettext("Please specify your preferred language.")}
          </Form.Control.Feedback>
        </Form.Group>
      )}
    </>
  );
}
