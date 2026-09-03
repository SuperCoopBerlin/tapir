import React, { ReactNode, useEffect, useRef, useState } from "react";
import { Card } from "react-bootstrap";
import Success from "./Success.tsx";
import Error from "./Error.tsx";
import { PreferredLanguage, RegistrationStage } from "./constants.ts";
import { getNavigatorLanguage } from "./util.ts";
import Step1IndividualOrCompany from "./steps/Step1IndividualOrCompany.tsx";
import Step2Membership from "./steps/Step2Membership.tsx";
import Step3PersonalDetails from "./steps/Step3PersonalDetails.tsx";
import Step4Legal from "./steps/Step4Legal.tsx";

declare let gettext: (english_text: string) => string;

const MemberRegistration: React.FC = () => {
  const [stage, setStage] = useState<RegistrationStage>(
    RegistrationStage.INDIVIDUAL_OR_COMPANY,
  );

  const [shares, setShares] = useState(1);
  const [ratenzahlung, setRatenzahlung] = useState(false);
  const [isCompany, setIsCompany] = useState(false);
  const [isInvesting, setIsInvesting] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const [companyName, setCompanyName] = useState("");
  const [preferredName, setPreferredName] = useState("");
  const [pronouns, setPronouns] = useState("");
  const [dob, setDOB] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState(
    getNavigatorLanguage() || PreferredLanguage.GERMAN,
  );

  const [street, setStreet] = useState("");
  const [city, setCity] = useState("Berlin");
  const [postcode, setPostcode] = useState("");
  const [country, setCountry] = useState("DE");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  const [errorMessage, setErrorMessage] = useState<ReactNode>("");
  const topRef = useRef<HTMLHeadingElement | null>(null);

  const configElement = document.getElementById("self_registration_config");
  const sharePrice = parseFloat(configElement?.dataset.sharePrice ?? "-1");
  const membershipFee = parseFloat(
    configElement?.dataset.membershipFee ?? "-1",
  );
  const coopName = configElement?.dataset.coopName ?? "NAME NOT FOUND";
  const coopStreet = configElement?.dataset.coopStreet ?? "STREET NOT FOUND";
  const coopPlace = configElement?.dataset.coopPlace ?? "PLACE NOT FOUND";
  const emailAddressMemberOffice =
    configElement?.dataset.emailAddressMemberOffice ??
    "EMAIL ADDRESS NOT FOUND";

  useEffect(() => {
    if (!topRef.current) {
      return;
    }

    (topRef.current as HTMLHeadingElement).scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, [stage]);

  return (
    <Card>
      <Card.Header>
        <h5 ref={topRef}>{gettext("Become a SuperCoop Member!")}</h5>
      </Card.Header>
      <Card.Body>
        {stage === RegistrationStage.INDIVIDUAL_OR_COMPANY && (
          <Step1IndividualOrCompany
            isCompany={isCompany}
            setIsCompany={setIsCompany}
            setIsInvesting={setIsInvesting}
            setStage={setStage}
          />
        )}
        {stage === RegistrationStage.MEMBERSHIP && (
          <Step2Membership
            setStage={setStage}
            sharePrice={sharePrice}
            isInvesting={isInvesting}
            setIsInvesting={setIsInvesting}
            ratenzahlung={ratenzahlung}
            setRatenzahlung={setRatenzahlung}
            shares={shares}
            setShares={setShares}
            isCompany={isCompany}
          />
        )}
        {stage === RegistrationStage.PERSONAL_DETAILS && (
          <Step3PersonalDetails
            isCompany={isCompany}
            setStage={setStage}
            firstName={firstName}
            setFirstName={setFirstName}
            lastName={lastName}
            setLastName={setLastName}
            preferredName={preferredName}
            setPreferredName={setPreferredName}
            pronouns={pronouns}
            setPronouns={setPronouns}
            dob={dob}
            setDOB={setDOB}
            preferredLanguage={preferredLanguage}
            setPreferredLanguage={setPreferredLanguage}
            isInvesting={isInvesting}
            companyName={companyName}
            setCompanyName={setCompanyName}
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
        )}
        {stage === RegistrationStage.LEGAL && (
          <Step4Legal
            isCompany={isCompany}
            setStage={setStage}
            firstName={firstName}
            lastName={lastName}
            preferredName={preferredName}
            pronouns={pronouns}
            dob={dob}
            preferredLanguage={preferredLanguage}
            isInvesting={isInvesting}
            companyName={companyName}
            street={street}
            postcode={postcode}
            city={city}
            country={country}
            email={email}
            phone={phone}
            shares={0}
            sharePrice={0}
            setErrorMessage={setErrorMessage}
            coopName={coopName}
            coopStreet={coopStreet}
            coopPlace={coopPlace}
            membershipFee={membershipFee}
            ratenzahlung={ratenzahlung}
            emailAddressMemberOffice={emailAddressMemberOffice}
          />
        )}
        {stage === RegistrationStage.SUCCESS && (
          <Success
            name={preferredName || [firstName, lastName].join(" ")}
            emailAddressMemberOffice={emailAddressMemberOffice}
          />
        )}
        {stage === RegistrationStage.ERROR && (
          <Error errorMessage={errorMessage} />
        )}
      </Card.Body>
    </Card>
  );
};

export default MemberRegistration;
