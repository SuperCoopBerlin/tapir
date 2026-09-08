import { Col, Form, Row } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

type Props = {
  firstName: string;
  setFirstName: React.Dispatch<React.SetStateAction<string>>;
  lastName: string;
  setLastName: React.Dispatch<React.SetStateAction<string>>;
  shares: number;
  setShares: React.Dispatch<React.SetStateAction<number>>;
  isInvesting: boolean;
  setIsInvesting: React.Dispatch<React.SetStateAction<boolean>>;
  ratenzahlung: boolean;
  setRatenzahlung: React.Dispatch<React.SetStateAction<boolean>>;
  sharePrice: number;
};

export default function Membership({
  firstName,
  setFirstName,
  lastName,
  setLastName,
  shares,
  setShares,
  isInvesting,
  setIsInvesting,
  ratenzahlung,
  setRatenzahlung,
  sharePrice,
}: Props) {
  return (
    <>
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
        <Form.Text>
          {gettext(
            `Investing members are supporters of the Cooperative. They cannot vote in the General Assembly and cannot use the services of the Cooperative.`,
          )}
        </Form.Text>
      </Form.Group>
      <h6 className="mt-4 mb-3">{gettext("Personal details")}</h6>
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
    </>
  );
}
