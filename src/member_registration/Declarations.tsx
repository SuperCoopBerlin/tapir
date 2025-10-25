import { Form } from "react-bootstrap";
import { MEMBERSHIP_FEE, SHARE_PRICE, COOP_NAME } from "./constants";
import DataProcessingAgreement from "./DataProcessingAgreement";

declare let gettext: (english_text: string) => string;

type Props = {
  name: string;
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
};

export default function Declarations({
  name,
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
}: Props) {
  return (
    <>
      <h6 className="mt-4 mb-3">{gettext("Declarations")}</h6>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-membership"
          label={`${gettext("I hereby request membership in the SuperCoop. I would like to take part with")} ${shares} ${gettext("share(s).")}`}
          //           label={gettext(`
          // Ich beantrage hiermit die Aufnahme in die SuperCoop. Ich möchte mich mit insgesamt ${shares} Anteil(en) an der Genossenschaft beteiligen.
          // `)}
          checked={acceptsMembership}
          name="accepts-membership"
          onChange={(event) => setAcceptsMembership(event.target.checked)}
          required
        />
        <p className="ms-4 mt-2">
          {gettext(
            "In accordance with the bylaws and the law, I agree to purchase shares at a price of",
            // "Ich verpflichte mich, die nach Satzung und Gesetz vorgesehenen Zahlungen in Höhe von",
          )}{" "}
          <strong>{SHARE_PRICE}€</strong>
          {gettext(" per share, as well as the membership fee of ")}
          {/*{gettext(" je Geschäftsanteil plus einem Eintrittsgeld in Höhe von ")}*/}
          <strong>{MEMBERSHIP_FEE}€</strong>
          {gettext(
            ", which will be used to cover administrative costs. I agree to transfer ",
            // " zu leisten, das der Deckung von Verwaltungskosten dient. Insgesamt verpflichte ich mich daher, ",
          )}{" "}
          <strong>{shares * SHARE_PRICE + MEMBERSHIP_FEE}€</strong>
          {gettext(" in total")}.{/*{gettext(" zu leisten")}.*/}
        </p>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-constitution"
          label={gettext(
            `I have been provided with a copy of the Bylaws of SuperCoop (either in digital or print form), which can be accessed below:`,
          )}
          // label={gettext(`Die Satzung von SuperCoop ist mir (entweder digital oder in gedruckter Form) ausgehändigt worden kann hier eingesehen werden:`)}
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
          //           label={gettext(`
          // Ich nehme zur Kenntnis, dass die Satzung eine Kündigungsfrist von 3 Jahren zum Ende des Geschäftsjahres
          // bestimmt. Die lange Laufzeit dient zur finanziellen Stabilität und ist ein wesentlicher Kern des
          // Genossenschaftsprinzips, das auf langfristige Ziele ausgerichtet ist. Eine Übertragung von Geschäftsanteilen
          // ist auch vorher bereits möglich und in der Satzung geregelt.
          // `)}
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
          // label={gettext(`Ich werde meine (Rest-)Zahlungen per Überweisung leisten und auf folgendes Konto überweisen:`)}
          checked={acceptsPayment}
          name="accepts-payment"
          onChange={(event) => setAcceptsPayment(event.target.checked)}
          required
        />
        <p className="ms-4 mt-2">
          <strong>{gettext("Account Owner")}:</strong> {COOP_NAME}
          <br />
          <strong>IBAN:</strong> DE98 4306 0967 1121 3790 00
          <br />
          <strong>BIC:</strong> GENODEM1GLS
          <br />
          <strong>{gettext("Subject")}:</strong>{" "}
          <em>{name}: Anteil und Eintrittsgeld</em>
          <br />
        </p>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Check
          type={"checkbox"}
          id="accepts-privacy"
          label={gettext(`
I accept the Data Processing Agreement listed below:
`)}
          //           label={gettext(`
          // Ich nehme die Datenschutzerklärung zur Kenntnis:
          // `)}
          checked={acceptsPrivacy}
          name="accepts-privacy"
          onChange={(event) => setAcceptsPrivacy(event.target.checked)}
          required
        />
        <DataProcessingAgreement />
      </Form.Group>
    </>
  );
}
