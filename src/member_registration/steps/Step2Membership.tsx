import React, { useState } from "react";
import { Form } from "react-bootstrap";
import { ChevronLeft, ChevronRight } from "react-bootstrap-icons";
import { RegistrationStage } from "../constants.ts";
import TapirButton from "../../components/TapirButton.tsx";

declare let gettext: (english_text: string) => string;

type Props = {
  shares: number;
  setShares: React.Dispatch<React.SetStateAction<number>>;
  sharePrice: number;
  ratenzahlung: boolean;
  setRatenzahlung: React.Dispatch<React.SetStateAction<boolean>>;
  isInvesting: boolean;
  setIsInvesting: React.Dispatch<React.SetStateAction<boolean>>;
  setStage: React.Dispatch<React.SetStateAction<RegistrationStage>>;
  isCompany: boolean;
};

const Step2Membership: React.FC<Props> = ({
  shares,
  setShares,
  sharePrice,
  ratenzahlung,
  setRatenzahlung,
  isInvesting,
  setIsInvesting,
  setStage,
  isCompany,
}: Props) => {
  const [validated, setValidated] = useState(false);

  return (
    <Form
      noValidate
      validated={validated}
      className={"mt-2"}
      style={{ width: "100%", maxWidth: "700px" }}
      autoComplete="on"
    >
      <h5>{gettext("Step 2 - Your Membership")}</h5>
      <Form.Group className={"mt-2"}>
        <Form.Label>
          {gettext("How many shares would you like to join with?")}
        </Form.Label>
        <Form.Control
          type={"number"}
          value={shares}
          name="shares"
          min="1"
          max="1000"
          style={{ width: "auto" }}
          onChange={(event) => setShares(parseInt(event.target.value))}
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext("You have to join with 1 or more shares.")}
        </Form.Control.Feedback>
        <Form.Text className="mt-2">
          {gettext("You are joining with")}{" "}
          <strong>{shares * sharePrice}€</strong> {gettext("worth of shares.")}
        </Form.Text>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>
          {gettext("Would you like to pay by instalments?")}
        </Form.Label>
        <Form.Check
          type={"radio"}
          id="ratenzahlung-active"
          label={gettext("Yes")}
          checked={ratenzahlung}
          name="ratenzahlung"
          onChange={(event) => setRatenzahlung(event.target.checked)}
        />
        <Form.Check
          type={"radio"}
          id="ratenzahlung-inactive"
          label={gettext("No")}
          checked={!ratenzahlung}
          name="ratenzahlung"
          onChange={(event) => setRatenzahlung(!event.target.checked)}
        />
        <Form.Text className="mt-2">
          {gettext(
            "You can pay your share(s) over several months instead of in one payment.",
          )}
        </Form.Text>
      </Form.Group>
      {!isCompany && (
        <>
          <h6 className="mt-4 mb-3">
            {gettext("Choose your membership type")}
          </h6>
          <Form.Group className={"mt-2"}>
            <Form.Check
              type={"radio"}
              id="membership-active"
              label={gettext("Active member")}
              checked={!isInvesting}
              name="investing"
              onChange={(event) => setIsInvesting(!event.target.checked)}
              required
            />
            <Form.Check
              type={"radio"}
              id="membership-investing"
              label={gettext("Investing member")}
              checked={isInvesting}
              name="investing"
              onChange={(event) => setIsInvesting(event.target.checked)}
              required
            />
            <Form.Text>
              {gettext(
                `Investing members are supporters of the Cooperative. They cannot vote in the General Assembly and cannot use the services of the Cooperative.`,
              )}
            </Form.Text>
          </Form.Group>
        </>
      )}
      <div className={"mt-5"} style={{ display: "flex", gap: "0.5rem" }}>
        <TapirButton
          icon={ChevronLeft}
          text={gettext("Back")}
          variant={"secondary"}
          onClick={() => setStage(RegistrationStage.INDIVIDUAL_OR_COMPANY)}
        />
        <TapirButton
          icon={ChevronRight}
          text={gettext("Next - Personal details")}
          variant={"primary"}
          onClick={(event) => {
            event.preventDefault();
            if (!event.currentTarget.form?.checkValidity()) {
              setValidated(true);
              return;
            }

            setValidated(false);
            setStage(RegistrationStage.PERSONAL_DETAILS);
          }}
        />
      </div>
    </Form>
  );
};

export default Step2Membership;
