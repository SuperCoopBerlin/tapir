import React, { useState } from "react";
import { Card, Form } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { CoopApi } from "../api-client/index.ts";
import TapirButton from "../components/TapirButton.tsx";
import { ChevronLeft, ChevronRight, Send } from "react-bootstrap-icons";
import PersonalInfo from "./form_parts/PersonalInfo.tsx";
import CompanyInfo from "./form_parts/CompanyInfo.tsx";
import Membership from "./form_parts/Membership.tsx";
import JoiningAs from "./form_parts/JoiningAs.tsx";
import ContactInfo from "./form_parts/ContactInfo.tsx";
import Overview from "./Overview.tsx";
import Declarations from "./Declarations.tsx";
import Intro from "./Intro.tsx";

declare let gettext: (english_text: string) => string;

enum RegistrationStage {
  ONE,
  TWO,
}

const MemberRegistration: React.FC = () => {
  const coopApi = useApi(CoopApi);
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");

  const [preferredName, setPreferredName] = useState("");
  const [pronouns, setPronouns] = useState("");
  const [dob, setDOB] = useState("");

  const [email, setEmail] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [postcode, setPostcode] = useState("");
  const [country, setCountry] = useState("");
  const [phone, setPhone] = useState("");
  const [shares, setShares] = useState(1);
  const [loading, setLoading] = useState(false);
  const [isCompany, setIsCompany] = useState<boolean | null>(null);
  const [isInvesting, setIsInvesting] = useState(false);
  const [stage, setStage] = useState<RegistrationStage>(RegistrationStage.ONE);
  const [acceptsMembership, setAcceptsMembership] = useState(false);
  const [acceptsPeriod, setAcceptsPeriod] = useState(false);
  const [acceptsConstitution, setAcceptsConstitution] = useState(false);
  const [acceptsPayment, setAcceptsPayment] = useState(false);
  const [acceptsPrivacy, setAcceptsPrivacy] = useState(false);
  const [otherComments, setOtherComments] = useState("");
  const [validated, setValidated] = useState(false);

  function onConfirmRegister() {
    setLoading(true);

    coopApi
      .coopMemberSelfRegisterCreate({
        memberRegistrationRequest: {
          email: email,
          firstName: "placeholder",
          lastName: "placeholder",
          numberOfCoopShares: -1,
        },
      })
      .then((result) => {
        if (result) {
          alert("Success!");
        } else {
          alert("Failed!");
        }
      })
      .catch((error) => {
        alert("Request failed! Check the console log");
        console.error(error);
      })
      .finally(() => setLoading(false));
  }

  return (
    <Card>
      <Card.Header>
        <h5>{gettext("Become a SuperCoop Member!")}</h5>
      </Card.Header>
      <Card.Body>
        <Intro />
        {stage === RegistrationStage.ONE && (
          <Form
            noValidate
            validated={validated}
            className={"mt-2"}
            style={{ width: "100%", maxWidth: "700px" }}
            autoComplete="on"
          >
            <h5>{gettext("Step 1 - Your Membership")}</h5>
            <JoiningAs
              isCompany={isCompany}
              setIsCompany={setIsCompany}
              setIsInvesting={setIsInvesting}
            />
            {isCompany !== null && (
              <>
                <Membership
                  name={name}
                  setName={setName}
                  shares={shares}
                  setShares={setShares}
                  isInvesting={isInvesting}
                  setIsInvesting={setIsInvesting}
                />
                {!isCompany && (
                  <PersonalInfo
                    preferredName={preferredName}
                    setPreferredName={setPreferredName}
                    pronouns={pronouns}
                    setPronouns={setPronouns}
                    dob={dob}
                    setDOB={setDOB}
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
                <Form.Group className={"mt-5"}>
                  <TapirButton
                    icon={ChevronRight}
                    text={gettext("Next - Overview & Declarations")}
                    variant={"primary"}
                    onClick={(event) => {
                      event.preventDefault();
                      if (!event.currentTarget.form?.checkValidity()) {
                        setValidated(true);
                        return;
                      }

                      setValidated(false);
                      setStage(RegistrationStage.TWO);
                    }}
                  />
                </Form.Group>
              </>
            )}
          </Form>
        )}
        {stage === RegistrationStage.TWO && (
          <Form
            className={"mt-2"}
            style={{ width: "100%", maxWidth: "700px" }}
            autoComplete="on"
            noValidate
            validated={validated}
          >
            <h5 className="mb-3">
              {gettext("Step 2 - Overview & Declarations")}
            </h5>
            <Overview
              isCompany={isCompany}
              name={name}
              preferredName={preferredName}
              pronouns={pronouns}
              dob={dob}
              companyName={companyName}
              street={street}
              postcode={postcode}
              city={city}
              country={country}
              email={email}
              phone={phone}
            />
            <Declarations
              name={name}
              shares={shares}
              acceptsMembership={acceptsMembership}
              setAcceptsMembership={setAcceptsMembership}
              acceptsPeriod={acceptsPeriod}
              setAcceptsPeriod={setAcceptsPeriod}
              acceptsConstitution={acceptsConstitution}
              setAcceptsConstitution={setAcceptsConstitution}
              acceptsPayment={acceptsPayment}
              setAcceptsPayment={setAcceptsPayment}
              acceptsPrivacy={acceptsPrivacy}
              setAcceptsPrivacy={setAcceptsPrivacy}
            />
            <hr></hr>
            <Form.Group className={"mt-2"}>
              <Form.Label>{gettext("Other comments")}</Form.Label>
              <Form.Control
                as="textarea"
                id="other-comments"
                placeholder={`(${gettext("e.g. payment in installments, including payment periods")})`}
                value={otherComments}
                name="other-comments"
                onChange={(event) => setOtherComments(event.target.value)}
              />
            </Form.Group>
            <div className={"mt-5"} style={{ display: "flex", gap: "0.5rem" }}>
              <TapirButton
                icon={ChevronLeft}
                text={gettext("Back")}
                variant={"secondary"}
                onClick={() => setStage(RegistrationStage.ONE)}
              />
              <TapirButton
                icon={Send}
                text={gettext("Submit your application")}
                variant={"primary"}
                onClick={(event) => {
                  event.preventDefault();
                  console.log("test", event.currentTarget.form);

                  if (!event.currentTarget.form?.checkValidity()) {
                    setValidated(true);
                    return;
                  }

                  onConfirmRegister();
                }}
                disabled={
                  !acceptsConstitution ||
                  !acceptsMembership ||
                  !acceptsPayment ||
                  !acceptsPeriod ||
                  !acceptsPrivacy
                }
                loading={loading}
              />
            </div>
          </Form>
        )}
      </Card.Body>
    </Card>
  );
};

export default MemberRegistration;
