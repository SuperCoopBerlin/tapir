import { Form } from "react-bootstrap";
import { SHARE_PRICE } from "../constants";

declare let gettext: (english_text: string) => string;

type Props = {
  name: string;
  setName: React.Dispatch<React.SetStateAction<string>>;
  shares: number;
  setShares: React.Dispatch<React.SetStateAction<number>>;
  isInvesting: boolean;
  setIsInvesting: React.Dispatch<React.SetStateAction<boolean>>;
};

export default function Membership({
  name,
  setName,
  shares,
  setShares,
  isInvesting,
  setIsInvesting,
}: Props) {
  return (
    <>
      <h6 className="mt-4 mb-3">{gettext("Choose your entry shares")}</h6>
      <Form.Group className={"mt-2"}>
        <Form.Label>
          {gettext("How many shares would you like to join with?")}
        </Form.Label>
        <Form.Control
          type={"number"}
          value={shares}
          name="shares"
          onChange={(event) => setShares(parseInt(event.target.value))}
          required
        />
        <p className="mt-2">
          {gettext("You are joining with")}{" "}
          <strong>{shares * SHARE_PRICE}€</strong> {gettext("worth of shares.")}
        </p>
      </Form.Group>
      <h6 className="mt-4 mb-3">{gettext("Choose your membership type")}</h6>
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
      </Form.Group>
      <p>
        {gettext(
          `Investing members are supporters of the Cooperative. They cannot vote in the General Assembly and cannot use the services of the Cooperative.`,
          // `Investierende Mitglieder sind fördernde Mitglieder. Sie haben kein Stimmrecht in der Generalversammlung und können die Leistungen der Genossenschaft nicht nutzen.`,
        )}
      </p>
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
    </>
  );
}
