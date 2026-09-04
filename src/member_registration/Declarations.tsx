import { Form } from "react-bootstrap";
import DataProcessingAgreement from "./DataProcessingAgreement";
import { useEffect, useMemo } from "react";
import { FriendlyCaptchaSDK } from "@friendlycaptcha/sdk";

declare let gettext: (english_text: string) => string;

type Props = {
  firstName: string;
  lastName: string;
  shares: number;
  acceptsMembership: boolean;
  setAcceptsMembership: React.Dispatch<React.SetStateAction<boolean>>;
  acceptsPeriod: boolean;
  setAcceptsPeriod: React.Dispatch<React.SetStateAction<boolean>>;
  acceptsConstitution: boolean;
  setAcceptsConstitution: React.Dispatch<React.SetStateAction<boolean>>;
  acceptsPayment: boolean;
  setAcceptsPayment: React.Dispatch<React.SetStateAction<boolean>>;
  acceptsPrivacy: boolean;
  setAcceptsPrivacy: React.Dispatch<React.SetStateAction<boolean>>;
  sharePrice: number;
  coopName: string;
  coopStreet: string;
  coopPlace: string;
  membershipFee: number;
  captchaSdk: FriendlyCaptchaSDK;
  setCaptchaResponse: React.Dispatch<React.SetStateAction<string>>;
  friendlyCaptchaSiteKey: string;
};

export default function Declarations({
  firstName,
  lastName,
  shares,
  acceptsMembership,
  setAcceptsMembership,
  acceptsPeriod,
  setAcceptsPeriod,
  acceptsConstitution,
  setAcceptsConstitution,
  acceptsPayment,
  setAcceptsPayment,
  acceptsPrivacy,
  setAcceptsPrivacy,
  sharePrice,
  coopName,
  coopStreet,
  coopPlace,
  membershipFee,
  captchaSdk,
  setCaptchaResponse,
  friendlyCaptchaSiteKey,
}: Props) {
  const paymentTotal = useMemo(
    () => shares * sharePrice + membershipFee,
    [shares, sharePrice, membershipFee],
  );

  useEffect(() => {
    const widget = captchaSdk.createWidget({
      element: document.getElementById("captcha")!,
      sitekey: friendlyCaptchaSiteKey,
    });

    widget.addEventListener("frc:widget.complete", (event) =>
      setCaptchaResponse(event.detail.response),
    );
    widget.addEventListener("frc:widget.error", () => setCaptchaResponse(""));
    widget.addEventListener("frc:widget.expire", () => setCaptchaResponse(""));
  }, [captchaSdk, setCaptchaResponse, friendlyCaptchaSiteKey]);

  return (
    <>
      <h6 className="mt-4 mb-3">{gettext("Declarations")}</h6>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-membership"
          label={`${gettext("I hereby request membership in the SuperCoop. I would like to take part with")} ${shares} ${gettext("share(s).")}`}
          checked={acceptsMembership}
          name="accepts-membership"
          onChange={(event) => setAcceptsMembership(event.target.checked)}
          required
        />
        <p className="ms-4 mt-2">
          {gettext(
            "In accordance with the bylaws and the law, I agree to purchase shares at a price of",
          )}{" "}
          <strong>{sharePrice}€</strong>
          {gettext(" per share, as well as the membership fee of ")}
          <strong>{membershipFee}€</strong>
          {gettext(
            ", which will be used to cover administrative costs. I agree to transfer ",
          )}{" "}
          <strong>{paymentTotal}€</strong>
          {gettext(" in total")}.
        </p>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-constitution"
          label={gettext(
            `I have been provided with a copy of the Bylaws of SuperCoop (either in digital or print form), which can be accessed below:`,
          )}
          checked={acceptsConstitution}
          name="accepts-constitution"
          onChange={(event) => setAcceptsConstitution(event.target.checked)}
          required
        />
        <p className="ms-4 mt-2">
          <a href="https://supercoop.de/unsere-genossenschaft/" target="_blank">
            SuperCoop - {gettext("Bylaws")}
          </a>
        </p>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-period"
          label={gettext(`
I accept that the Bylaws set a minimum membership period of three years, up to the end of the third accounting year.
The long membership period helps secure financial stability and is an important part of the cooperative principle,
which is oriented towards long-term goals. A transfer of shares in the Cooperative in accordance with the Bylaws is allowed before the
end of the minimum membership period.
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
          label={gettext(
            `I agree to pay the payment(s) via bank transfer to the account specified below:`,
          )}
          checked={acceptsPayment}
          name="accepts-payment"
          onChange={(event) => setAcceptsPayment(event.target.checked)}
          required
        />
        <p className="ms-4 mt-2">
          <strong>{gettext("Account Owner")}:</strong> {coopName}
          <br />
          <strong>IBAN:</strong> DE98 4306 0967 1121 3790 00
          <br />
          <strong>BIC:</strong> GENODEM1GLS
          <br />
          <strong>{gettext("Subject")}:</strong>{" "}
          <em>{[firstName, lastName].join(" ")}: Anteil und Eintrittsgeld</em>
          <br />
          <strong>{gettext("Amount")}:</strong> {paymentTotal}€
          <br />
        </p>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-privacy"
          label={gettext(
            "I accept the Data Processing Agreement listed below:",
          )}
          checked={acceptsPrivacy}
          name="accepts-privacy"
          onChange={(event) => setAcceptsPrivacy(event.target.checked)}
          required
        />
        <DataProcessingAgreement
          coopName={coopName}
          coopStreet={coopStreet}
          coopPlace={coopPlace}
        />
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <div id={"captcha"} />
      </Form.Group>
    </>
  );
}
