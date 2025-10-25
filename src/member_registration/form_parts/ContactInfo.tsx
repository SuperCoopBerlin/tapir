import { Form } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

type Props = {
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

export default function ContactInfo({
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
}: Props) {
  return (
    <>
      <h6 className="mt-4 mb-3">{gettext("Address & Contact Info")}</h6>
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
    </>
  );
}
