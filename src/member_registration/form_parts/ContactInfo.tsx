import { Form } from "react-bootstrap";
import { countries } from "../constants";
import { useEffect, useRef, useState } from "react";
import { isPossiblePhoneNumber } from "libphonenumber-js";

declare let gettext: (english_text: string) => string;

const displayNames = new Intl.DisplayNames(
  [document.documentElement.getAttribute("lang") ?? navigator.language],
  {
    type: "region",
  },
);

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
  const [emailVerification, setEmailVerification] = useState("");
  const emailVerificationRef = useRef<HTMLInputElement | null>(null);
  const phoneRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (
      !emailVerificationRef.current ||
      email === "" ||
      emailVerification === ""
    ) {
      return;
    }
    emailVerificationRef.current.setCustomValidity(
      email === emailVerification
        ? ""
        : gettext("Both email addresses must be the same"),
    );
  }, [email, emailVerification]);

  useEffect(() => {
    if (!phoneRef.current) {
      return;
    }
    phoneRef.current.setCustomValidity(
      isPossiblePhoneNumber(phone, "DE") ? "" : gettext("Invalid phone number"),
    );
  }, [phone]);

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
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext("Please specify the street address.")}
        </Form.Control.Feedback>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("Postcode")}</Form.Label>
        <Form.Control
          type="text"
          value={postcode}
          autoComplete="postal-code"
          name="postcode"
          onChange={(event) => setPostcode(event.target.value)}
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext("Please specify the postal code.")}
        </Form.Control.Feedback>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("City")}</Form.Label>
        <Form.Control
          type="text"
          value={city}
          name="city"
          autoComplete="address-level2"
          onChange={(event) => setCity(event.target.value)}
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext("Please specify the town or city name.")}
        </Form.Control.Feedback>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("Country")}</Form.Label>
        <Form.Select
          value={country}
          name="country"
          autoComplete="country"
          onChange={(event) => setCountry(event.target.value)}
          required
        >
          {countries.map((code) => (
            <option key={code} value={code}>
              {displayNames.of(code)}
            </option>
          ))}
        </Form.Select>
        <Form.Control.Feedback type="invalid">
          {gettext("Please specify the country name.")}
        </Form.Control.Feedback>
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
        <Form.Control.Feedback type="invalid">
          {gettext("Please provide a valid e-mail address.")}
        </Form.Control.Feedback>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("E-mail (verification)")}</Form.Label>
        <Form.Control
          ref={emailVerificationRef}
          type={"email"}
          value={emailVerification}
          name="emailVerification"
          onChange={(event) => setEmailVerification(event.target.value)}
          autoComplete="email"
          required
        />
        <Form.Control.Feedback type="invalid">
          {gettext("The two email addresses are different")}
        </Form.Control.Feedback>
      </Form.Group>
      <Form.Group className={"mt-2"}>
        <Form.Label>{gettext("Phone number")}</Form.Label>
        <Form.Control
          ref={phoneRef}
          type={"tel"}
          value={phone}
          name="phone"
          onChange={(event) => setPhone(event.target.value)}
        />
        <Form.Control.Feedback type="invalid">
          {gettext("Invalid phone number")}
        </Form.Control.Feedback>
        <Form.Text>
          {gettext(
            "German phone number don't need a prefix (e.g. (0)1736160646), international always (e.g. +12125552368)",
          )}
        </Form.Text>
      </Form.Group>
    </>
  );
}
