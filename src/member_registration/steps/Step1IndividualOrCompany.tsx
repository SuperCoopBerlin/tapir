import React from "react";
import { Form } from "react-bootstrap";
import TapirButton from "../../components/TapirButton.tsx";
import { ChevronRight } from "react-bootstrap-icons";
import { RegistrationStage } from "../constants.ts";

declare let gettext: (english_text: string) => string;

type Props = {
  isCompany: boolean;
  setIsCompany: React.Dispatch<React.SetStateAction<boolean>>;
  setIsInvesting: React.Dispatch<React.SetStateAction<boolean>>;
  setStage: React.Dispatch<React.SetStateAction<RegistrationStage>>;
};

const Step1IndividualOrCompany: React.FC<Props> = ({
  isCompany,
  setIsCompany,
  setIsInvesting,
  setStage,
}: Props) => {
  return (
    <>
      <h5>{gettext("Step 1")}</h5>
      <Form>
        <Form.Group className={"mt-3 mb-3"}>
          <h6 className="mt-4 mb-3">
            {gettext("Are you joining as an individual or company?")}
          </h6>
          <Form.Check
            type={"radio"}
            id="joining-as-individual"
            label={gettext("Individual")}
            checked={!isCompany}
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
            checked={isCompany}
            name="joiningAs"
            onChange={(event) => {
              setIsCompany(event.target.checked);
              setIsInvesting(event.target.checked);
            }}
            required
          />
        </Form.Group>
        <Form.Group className={"mt-5"}>
          <TapirButton
            icon={ChevronRight}
            text={gettext("Next - Your membership")}
            variant={"primary"}
            onClick={(event) => {
              event.preventDefault();
              setStage(RegistrationStage.MEMBERSHIP);
            }}
          />
        </Form.Group>
      </Form>
    </>
  );
};

export default Step1IndividualOrCompany;
