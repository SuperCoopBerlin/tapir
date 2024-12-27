import React from "react";
import { ShareOwnerForWelcomeDesk } from "../api-client";
import { Card } from "react-bootstrap";

declare let gettext: (english_text: string) => string;

interface WelcomeDeskMemberDetailsProps {
  selectedMember: ShareOwnerForWelcomeDesk;
}

const WelcomeDeskMemberDetails: React.FC<WelcomeDeskMemberDetailsProps> = ({
  selectedMember,
}) => {
  function getDetailCardColor(member: ShareOwnerForWelcomeDesk) {
    if (!member.canShop) return "danger";
    if (member.warnings.length > 0) return "warning";
    return "success";
  }

  return (
    <Card className={"text-bg-" + getDetailCardColor(selectedMember)}>
      <Card.Header>
        <h5>{gettext("Member details")}</h5>
      </Card.Header>
      <Card.Body>
        <div>
          {gettext("Member")}: {selectedMember.displayName}
        </div>
        <div>
          {gettext("Can shop")}:{" "}
          {selectedMember.canShop ? gettext("yes") : gettext("no")}
        </div>
        {selectedMember.warnings.length > 0 && (
          <div>
            Warnings:{" "}
            <ul>
              {selectedMember.warnings.map((warning, index) => {
                return <li key={index}>{warning}</li>;
              })}
            </ul>
          </div>
        )}
        {selectedMember.reasonsCannotShop.length > 0 && (
          <div>
            {gettext("Why this member cannot shop: ")}
            <ul>
              {selectedMember.reasonsCannotShop.map((reason, index) => {
                return <li key={index}>{reason}</li>;
              })}
            </ul>
          </div>
        )}
        <div>
          {gettext("Co-purchaser: ")}
          {selectedMember.coPurchaser
            ? selectedMember.coPurchaser
            : gettext("None")}
        </div>
      </Card.Body>
    </Card>
  );
};

export default WelcomeDeskMemberDetails;
