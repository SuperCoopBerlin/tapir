import React, { ReactNode, useCallback, useState } from "react";
import { Form } from "react-bootstrap";
import { ChevronLeft, Send } from "react-bootstrap-icons";
import { PreferredLanguage, RegistrationStage } from "../constants.ts";
import TapirButton from "../../components/TapirButton.tsx";
import Overview from "../Overview.tsx";
import Declarations from "../Declarations.tsx";
import {
  CoopApi,
  CountryEnum,
  MemberRegistrationRequest,
} from "../../api-client";
import { useApi } from "../../hooks/useApi.ts";

declare let gettext: (english_text: string) => string;

type Props = {
  shares: number;
  sharePrice: number;
  setStage: React.Dispatch<React.SetStateAction<RegistrationStage>>;
  setErrorMessage: React.Dispatch<React.SetStateAction<ReactNode>>;
  isCompany: boolean;
  isInvesting: boolean;
  firstName: string;
  lastName: string;
  preferredName: string;
  pronouns: string;
  dob: string;
  preferredLanguage: PreferredLanguage;
  companyName: string;
  street: string;
  postcode: string;
  city: string;
  country: string;
  email: string;
  phone: string;
  coopName: string;
  coopStreet: string;
  coopPlace: string;
  membershipFee: number;
  ratenzahlung: boolean;
  emailAddressMemberOffice: string;
};

const Step4Legal: React.FC<Props> = ({
  shares,
  sharePrice,
  setStage,
  isCompany,
  isInvesting,
  preferredLanguage,
  firstName,
  lastName,
  preferredName,
  pronouns,
  dob,
  companyName,
  street,
  postcode,
  city,
  country,
  email,
  phone,
  coopName,
  coopStreet,
  coopPlace,
  membershipFee,
  ratenzahlung,
  emailAddressMemberOffice,
  setErrorMessage,
}: Props) => {
  const coopApi = useApi(CoopApi);

  const [loading, setLoading] = useState(false);

  const [acceptsMembership, setAcceptsMembership] = useState(false);
  const [acceptsPeriod, setAcceptsPeriod] = useState(false);
  const [acceptsConstitution, setAcceptsConstitution] = useState(false);
  const [acceptsPayment, setAcceptsPayment] = useState(false);
  const [acceptsPrivacy, setAcceptsPrivacy] = useState(false);

  const [validated, setValidated] = useState(false);

  const onConfirmRegister = useCallback(() => {
    setLoading(true);

    const memberRegistrationRequest: MemberRegistrationRequest = {
      firstName,
      lastName,
      isCompany: isCompany,
      isInvesting,
      numShares: shares,

      birthdate: isCompany ? new Date() : new Date(dob),
      usageName: preferredName,
      pronouns,
      preferredLanguage,

      street,
      city,
      postcode,
      country: country as CountryEnum,

      email,
      phone,
      ratenzahlung,
    };

    if (companyName) memberRegistrationRequest.companyName = companyName;

    coopApi
      .coopMemberSelfRegisterCreate({
        memberRegistrationRequest,
      })
      .then((result) => {
        if (result) {
          setStage(RegistrationStage.SUCCESS);
        } else {
          setStage(RegistrationStage.ERROR);
        }
      })
      .catch(async (error) => {
        setStage(RegistrationStage.ERROR);
        let newErrorMessage;
        if (error.response.status < 500) {
          newErrorMessage = await error.response.json();
        } else {
          console.error(error);
          newErrorMessage = (
            <p>
              {gettext(
                `Please try again later. If you keep having issues, please contact the Members Office at`,
              )}{" "}
              <a href={`mailto:${emailAddressMemberOffice}`}>
                {emailAddressMemberOffice}
              </a>
            </p>
          );
        }
        setErrorMessage(newErrorMessage);
      })
      .finally(() => setLoading(false));
  }, [
    city,
    companyName,
    coopApi,
    country,
    dob,
    email,
    emailAddressMemberOffice,
    firstName,
    isCompany,
    isInvesting,
    lastName,
    phone,
    postcode,
    preferredLanguage,
    preferredName,
    pronouns,
    ratenzahlung,
    setErrorMessage,
    setStage,
    shares,
    street,
  ]);

  return (
    <Form
      className={"mt-2"}
      style={{ width: "100%", maxWidth: "700px" }}
      autoComplete="on"
      noValidate
      validated={validated}
    >
      <h5 className="mb-3">{gettext("Step 4 - Overview & Declarations")}</h5>
      <Overview
        isCompany={isCompany}
        firstName={firstName}
        lastName={lastName}
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
        firstName={firstName}
        lastName={lastName}
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
        sharePrice={sharePrice}
        coopName={coopName}
        coopStreet={coopStreet}
        coopPlace={coopPlace}
        membershipFee={membershipFee}
      />
      <hr></hr>
      <div className={"mt-5"} style={{ display: "flex", gap: "0.5rem" }}>
        <TapirButton
          icon={ChevronLeft}
          text={gettext("Back")}
          variant={"secondary"}
          onClick={() => setStage(RegistrationStage.PERSONAL_DETAILS)}
        />
        <TapirButton
          icon={Send}
          text={gettext("Submit your application")}
          variant={"primary"}
          onClick={(event) => {
            event.preventDefault();

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
  );
};

export default Step4Legal;
