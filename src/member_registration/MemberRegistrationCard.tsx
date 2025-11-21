import React, { useState } from "react";
import { Card, Form } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { CoopApi } from "../api-client";
import TapirButton from "../components/TapirButton.tsx";
import { Floppy } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const MemberRegistrationCard: React.FC = () => {
  const coopApi = useApi(CoopApi);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

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
      });
  }

  return (
    <Card>
      <Card.Header>
        <h5>{gettext("Member self register")}</h5>
      </Card.Header>
      <Card.Body>
        <div>Hello Hackathon :)</div>
        <Form className={"mt-2"}>
          <Form.Group>
            <Form.Label>E-Mail</Form.Label>
            <Form.Control
              type={"email"}
              placeholder={"E-Mail"}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Form.Group>
        </Form>
        <div className={"mt-2"}>
          <TapirButton
            icon={Floppy}
            text={"Register"}
            variant={"primary"}
            onClick={onConfirmRegister}
            disabled={email.length === 0}
            loading={loading}
          />
        </div>
      </Card.Body>
    </Card>
  );
};

export default MemberRegistrationCard;
