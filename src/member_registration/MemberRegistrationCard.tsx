import React, { useState } from "react";
import { Card, Form } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { CoopApi } from "../api-client";
import TapirButton from "../components/TapirButton.tsx";
import { ChevronLeft, ChevronRight, Send } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const SHARE_PRICE = 100;
const MEMBERSHIP_FEE = 10;

enum RegistrationStage {
  ONE,
  TWO,
}

const MemberRegistrationCard: React.FC = () => {
  const coopApi = useApi(CoopApi);
  const [name, setName] = useState("");
  const [preferredName, setPreferredName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [pronouns, setPronouns] = useState("");
  const [email, setEmail] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [postcode, setPostcode] = useState("");
  const [country, setCountry] = useState("");
  const [dob, setDOB] = useState("");
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
        <div className="mb-4">
          <p>
            <img
              style={{ width: "100%", maxWidth: "1000px" }}
              src="https://supercoop.de/wp-content/uploads/supercoop-header.jpg"
            />
          </p>
          <p>
            {gettext(`
  Welcome to SuperCoop! We're excited to welcome you as a new member of our cooperative.
  Please fill out the form below so we can process your application.
  `)}
          </p>
        </div>
        <Form
          className={"mt-2"}
          style={{ width: "100%", maxWidth: "700px" }}
          autoComplete="on"
        >
          {stage === RegistrationStage.ONE && (
            <>
              <h5>{gettext("Step 1 - Your Membership")}</h5>
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
              {isCompany !== null && (
                <>
                  <h6 className="mt-4 mb-3">
                    {gettext("Choose your entry shares")}
                  </h6>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>
                      {gettext("How many shares would you like to join with?")}
                    </Form.Label>
                    <Form.Control
                      type={"number"}
                      value={shares}
                      name="shares"
                      onChange={(event) =>
                        setShares(parseInt(event.target.value))
                      }
                      required
                    />
                    <p className="mt-2">
                      {gettext("You are joining with")}{" "}
                      <strong>{shares * SHARE_PRICE}€</strong>{" "}
                      {gettext("worth of shares.")}
                    </p>
                  </Form.Group>
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
                      onChange={(event) =>
                        setIsInvesting(!event.target.checked)
                      }
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
                  </Form.Group>
                  <p>Erklärung</p>
                  <h6 className="mt-4 mb-3">{gettext("Personal details")}</h6>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("What is your name?")}</Form.Label>
                    <Form.Control
                      type={"text"}
                      placeholder={gettext("First name and last name")}
                      value={name}
                      name="name"
                      onChange={(event) => setName(event.target.value)}
                      autoComplete="name"
                      required
                    />
                  </Form.Group>
                  {!isCompany && (
                    <>
                      <Form.Group className={"mt-2"}>
                        <Form.Label>
                          {gettext(
                            "How would you like to be addressed? (optional)",
                          )}
                        </Form.Label>
                        <Form.Control
                          type={"text"}
                          placeholder={gettext(
                            "Your preferred name or nickname",
                          )}
                          autoComplete="nickname"
                          name="nickname"
                          value={preferredName}
                          onChange={(event) =>
                            setPreferredName(event.target.value)
                          }
                        />
                      </Form.Group>
                      <Form.Group className={"mt-2"}>
                        <Form.Label>
                          {gettext("What are your pronouns?")}
                        </Form.Label>
                        <Form.Control
                          type={"text"}
                          placeholder={gettext("(Optional)")}
                          value={pronouns}
                          name="pronouns"
                          onChange={(event) => setPronouns(event.target.value)}
                        />
                      </Form.Group>
                      <Form.Group className={"mt-2"}>
                        <Form.Label>
                          {gettext("What is your date of birth?")}
                        </Form.Label>
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
                  )}
                  {isCompany && (
                    <Form.Group className={"mt-2"}>
                      <Form.Label>
                        {gettext("What is your company name?")}
                      </Form.Label>
                      <Form.Control
                        type={"text"}
                        placeholder={gettext(
                          "Please enter the official company name",
                        )}
                        name="companyName"
                        value={companyName}
                        onChange={(event) => setCompanyName(event.target.value)}
                        required
                      />
                    </Form.Group>
                  )}
                  <h6 className="mt-4 mb-3">
                    {gettext("What is your address?")}
                  </h6>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("Street & house number")}</Form.Label>
                    <Form.Control
                      type="text"
                      value={street}
                      autoComplete="street-address"
                      name="street"
                      onChange={(event) => setStreet(event.target.value)}
                    />
                  </Form.Group>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("Postcode")}</Form.Label>
                    <Form.Control
                      type="text"
                      value={postcode}
                      autoComplete="postal-code"
                      name="postcode"
                      onChange={(event) => setPostcode(event.target.value)}
                    />
                  </Form.Group>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("City")}</Form.Label>
                    <Form.Control
                      type="text"
                      value={city}
                      name="city"
                      autoComplete="address-level2"
                      onChange={(event) => setCity(event.target.value)}
                    />
                  </Form.Group>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("Country")}</Form.Label>
                    <Form.Control
                      type="text"
                      value={country}
                      name="country"
                      autoComplete="country-name"
                      onChange={(event) => setCountry(event.target.value)}
                    />
                  </Form.Group>
                  <h6 className="mt-4 mb-3">{gettext("Contact info")}</h6>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("E-mail")}</Form.Label>
                    <Form.Control
                      type={"email"}
                      value={email}
                      name="email"
                      onChange={(event) => setEmail(event.target.value)}
                      autoComplete="email"
                      required
                    />
                  </Form.Group>
                  <Form.Group className={"mt-2"}>
                    <Form.Label>{gettext("Phone number")}</Form.Label>
                    <Form.Control
                      type={"text"}
                      value={phone}
                      name="phone"
                      onChange={(event) => setPhone(event.target.value)}
                      autoComplete="tel"
                    />
                  </Form.Group>
                  <Form.Group className={"mt-5"}>
                    <TapirButton
                      icon={ChevronRight}
                      text={gettext("Next")}
                      variant={"primary"}
                      onClick={() => setStage(RegistrationStage.TWO)}
                    />
                  </Form.Group>
                </>
              )}
            </>
          )}
          {stage === RegistrationStage.TWO && (
            <div className="">
              <h5 className="mb-3">
                {gettext("Step 2 - Overview & Declarations")}
              </h5>
              <dl>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Name:")}</dt>
                  <dd>{name}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Preferred name:")}</dt>
                  <dd>{preferredName}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Pronouns:")}</dt>
                  <dd>{pronouns}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Date of birth:")}</dt>
                  <dd>{new Date(dob).toLocaleDateString()}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("E-mail:")}</dt>
                  <dd>{email}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Phone:")}</dt>
                  <dd>{phone}</dd>
                </div>
                <div style={{ display: "flex", gap: "1ch" }}>
                  <dt>{gettext("Address:")}</dt>
                  <dd>{[street, postcode, city, country].join(", ")}</dd>
                </div>
              </dl>
              <h6 className="mt-4 mb-3">{gettext("Declarations")}</h6>
              <Form.Group className={"mt-2"}>
                <Form.Check
                  type={"checkbox"}
                  id="accepts-membership"
                  label={gettext(`
Ich beantrage hiermit die Aufnahme in die SuperCoop. Ich möchte mich mit insgesamt ${shares} Anteil(en) an der Genossenschaft beteiligen.
`)}
                  checked={acceptsMembership}
                  name="accepts-membership"
                  onChange={(event) =>
                    setAcceptsMembership(event.target.checked)
                  }
                  required
                />
                <p className="ms-4 mt-2">
                  Ich verpflichte mich, die nach Satzung und Gesetz vorgesehenen
                  Zahlungen in Höhe von <strong>{SHARE_PRICE}€</strong> je
                  Geschäftsanteil plus einem Eintrittsgeld in Höhe von{" "}
                  <strong>{MEMBERSHIP_FEE}€</strong> zu leisten, das der Deckung
                  von Verwaltungskosten dient. Insgesamt verpflichte ich mich
                  daher,{" "}
                  <strong>{shares * SHARE_PRICE + MEMBERSHIP_FEE}€</strong> zu
                  leisten.
                </p>
              </Form.Group>
              <Form.Group className={"mt-2"}>
                <Form.Check
                  type={"checkbox"}
                  id="accepts-constitution"
                  label={gettext(`
  Die Satzung von SuperCoop ist mir (entweder digital oder in gedruckter Form) ausgehändigt worden kann hier eingesehen werden:
`)}
                  checked={acceptsConstitution}
                  name="accepts-constitution"
                  onChange={(event) =>
                    setAcceptsConstitution(event.target.checked)
                  }
                  required
                />
                <p className="ms-4 mt-2">
                  <a
                    href="https://supercoop.de/unsere-genossenschaft/"
                    target="_blank"
                  >
                    SuperCoop - Satzung
                  </a>
                </p>
              </Form.Group>
              <Form.Group className={"mt-2"}>
                <Form.Check
                  type={"checkbox"}
                  id="accepts-period"
                  label={gettext(`
Ich nehme zur Kenntnis, dass die Satzung eine Kündigungsfrist von 3 Jahren zum Ende des Geschäftsjahres
bestimmt. Die lange Laufzeit dient zur finanziellen Stabilität und ist ein wesentlicher Kern des
Genossenschaftsprinzips, das auf langfristige Ziele ausgerichtet ist. Eine Übertragung von Geschäftsanteilen
ist auch vorher bereits möglich und in der Satzung geregelt.
`)}
                  checked={acceptsPeriod}
                  name="accepts-period"
                  onChange={(event) => setAcceptsPeriod(event.target.checked)}
                  required
                />
              </Form.Group>
              <Form.Group className={"mt-2"}>
                <Form.Check
                  type={"checkbox"}
                  id="accepts-payment"
                  label={gettext(`
Ich werde meine (Rest-)Zahlungen per Überweisung leisten und auf folgendes Konto überweisen:
`)}
                  checked={acceptsPayment}
                  name="accepts-payment"
                  onChange={(event) => setAcceptsPayment(event.target.checked)}
                  required
                />
                <p className="ms-4 mt-2">
                  <strong>Kontoinhaber:</strong> SuperCoop Berlin eG
                  <br />
                  <strong>IBAN:</strong> DE98 4306 0967 1121 3790 00
                  <br />
                  <strong>BIC:</strong> GENODEM1GLS
                  <br />
                  <strong>Betreff:</strong> {name}: Anteil und Eintrittsgeld
                  <br />
                </p>
              </Form.Group>
              <Form.Group className={"mt-2"}>
                <Form.Check
                  type={"checkbox"}
                  id="accepts-privacy"
                  label={gettext(`
Ich nehme die Datenschutzerklärung zur Kenntnis:
`)}
                  checked={acceptsPrivacy}
                  name="accepts-privacy"
                  onChange={(event) => setAcceptsPrivacy(event.target.checked)}
                  required
                />
                <p className="ms-4 mt-2">
                  <a
                    href="https://supercoop.de/Datenschutzerklaerung/"
                    target="_blank"
                  >
                    Datenschutzerklärung
                  </a>
                </p>
              </Form.Group>
              <Form.Group className={"mt-2"}>
                <Form.Label>Other comments</Form.Label>
                <Form.Control
                  as="textarea"
                  id="other-comments"
                  placeholder="(z.B. Ratenzahlung, wenn möglich mit Angabe der Zahlungsintervalle)"
                  value={otherComments}
                  name="other-comments"
                  onChange={(event) => setOtherComments(event.target.value)}
                  required
                />
              </Form.Group>
              <div
                className={"mt-5"}
                style={{ display: "flex", gap: "0.5rem" }}
              >
                <TapirButton
                  icon={ChevronLeft}
                  text={gettext("Back")}
                  variant={"secondary"}
                  onClick={() => setStage(RegistrationStage.ONE)}
                />
                <TapirButton
                  icon={Send}
                  text={gettext("Kostenpflichting absenden")}
                  variant={"primary"}
                  onClick={onConfirmRegister}
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
            </div>
          )}
        </Form>
      </Card.Body>
    </Card>
  );
};

export default MemberRegistrationCard;
