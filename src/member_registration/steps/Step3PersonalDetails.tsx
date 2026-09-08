import React, { useState } from "react";
import { Col, Form, Row } from "react-bootstrap";
import { ChevronLeft, ChevronRight } from "react-bootstrap-icons";
import { PreferredLanguage, RegistrationStage } from "../constants.ts";
import TapirButton from "../../components/TapirButton.tsx";
import PersonalInfo from "../form_parts/PersonalInfo.tsx";
import CompanyInfo from "../form_parts/CompanyInfo.tsx";
import ContactInfo from "../form_parts/ContactInfo.tsx";

declare let gettext: (english_text: string) => string;

type Props = {
  isCompany: boolean;
  setStage: React.Dispatch<React.SetStateAction<RegistrationStage>>;
  firstName: string;
  setFirstName: React.Dispatch<React.SetStateAction<string>>;
  lastName: string;
  setLastName: React.Dispatch<React.SetStateAction<string>>;
  preferredName: string;
  setPreferredName: React.Dispatch<React.SetStateAction<string>>;
  pronouns: string;
  setPronouns: React.Dispatch<React.SetStateAction<string>>;
  dob: string;
  setDOB: React.Dispatch<React.SetStateAction<string>>;
  preferredLanguage: PreferredLanguage;
  setPreferredLanguage: React.Dispatch<React.SetStateAction<PreferredLanguage>>;
  isInvesting: boolean;
  companyName: string;
  setCompanyName: React.Dispatch<React.SetStateAction<string>>;
  street: string;
  setStreet: React.Dispatch<React.SetStateAction<string>>;
  postcode: string;
  setPostcode: React.Dispatch<React.SetStateAction<string>>;
  city: string;
  setCity: React.Dispatch<React.SetStateAction<string>>;
  country: string;
  setCountry: React.Dispatch<React.SetStateAction<string>>;
  email: string;
  setEmail: React.Dispatch<React.SetStateAction<string>>;
  phone: string;
  setPhone: React.Dispatch<React.SetStateAction<string>>;
};

const Step3PersonalDetails: React.FC<Props> = ({
  isCompany,
  firstName,
  setFirstName,
  lastName,
  setLastName,
  setStage,
  preferredName,
  setPreferredName,
  pronouns,
  setPronouns,
  dob,
  setDOB,
  preferredLanguage,
  setPreferredLanguage,
  isInvesting,
  companyName,
  setCompanyName,
  street,
  setStreet,
  postcode,
  setPostcode,
  city,
  setCity,
  country,
  setCountry,
  email,
  setEmail,
  phone,
  setPhone,
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
      <h5>{gettext("Step 3 - Personal details")}</h5>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("What is your name?")}</Form.Label>
        <Row>
          <Col>
            <Form.Control
              type={"text"}
              placeholder={gettext("First name")}
              value={firstName}
              name="firstName"
              onChange={(event) => setFirstName(event.target.value)}
              autoComplete="first-name"
              required
            />
            <Form.Control.Feedback type="invalid">
              {gettext("Please specify your first name.")}
            </Form.Control.Feedback>
            <Form.Text>
              {gettext(
                'Please give your "administrative" name, as it is on your ID.',
              )}
            </Form.Text>
          </Col>
          <Col>
            <Form.Control
              type={"text"}
              placeholder={gettext("Last name")}
              value={lastName}
              name="lastName"
              onChange={(event) => setLastName(event.target.value)}
              autoComplete="last-name"
              required
            />
            <Form.Control.Feedback type="invalid">
              {gettext("Please specify your last name.")}
            </Form.Control.Feedback>
          </Col>
        </Row>
      </Form.Group>
      {!isCompany && (
        <PersonalInfo
          preferredName={preferredName}
          setPreferredName={setPreferredName}
          pronouns={pronouns}
          setPronouns={setPronouns}
          dob={dob}
          setDOB={setDOB}
          preferredLanguage={preferredLanguage}
          setPreferredLanguage={setPreferredLanguage}
          isInvesting={isInvesting}
        />
      )}
      {isCompany && (
        <CompanyInfo
          companyName={companyName}
          setCompanyName={setCompanyName}
        />
      )}
      <ContactInfo
        street={street}
        setStreet={setStreet}
        postcode={postcode}
        setPostcode={setPostcode}
        city={city}
        setCity={setCity}
        country={country}
        setCountry={setCountry}
        email={email}
        setEmail={setEmail}
        phone={phone}
        setPhone={setPhone}
      />
      <div className={"mt-5"} style={{ display: "flex", gap: "0.5rem" }}>
        <TapirButton
          icon={ChevronLeft}
          text={gettext("Back")}
          variant={"secondary"}
          onClick={() => setStage(RegistrationStage.MEMBERSHIP)}
        />
        <TapirButton
          icon={ChevronRight}
          text={gettext("Next - Legal")}
          variant={"primary"}
          onClick={(event) => {
            event.preventDefault();
            if (!event.currentTarget.form?.checkValidity()) {
              setValidated(true);
              return;
            }

            setValidated(false);
            setStage(RegistrationStage.LEGAL);
          }}
        />
      </div>
    </Form>
  );
};

export default Step3PersonalDetails;
