import React from "react";
import { Alert, Spinner, Table } from "react-bootstrap";
import { ShareOwnerForWelcomeDesk } from "../api-client";

declare let gettext: (english_text: string) => string;

interface WelcomeDeskSearchResultsProps {
  searchResults: ShareOwnerForWelcomeDesk[];
  loading: boolean;
  error: string;
  selectedMember: ShareOwnerForWelcomeDesk | undefined;
  setSelectedMember: (member: ShareOwnerForWelcomeDesk | undefined) => void;
}

const WelcomeDeskSearchResults: React.FC<WelcomeDeskSearchResultsProps> = ({
  searchResults,
  loading,
  error,
  selectedMember,
  setSelectedMember,
}) => {
  function buildSearchResults() {
    if (loading) return <Spinner />;

    if (error) return <Alert variant={"danger"}>{error}</Alert>;

    if (searchResults.length == 0) {
      return (
        <Alert variant={"primary"}>
          {gettext("Use the search field on the top right.")}
        </Alert>
      );
    }

    return buildResultList();
  }

  function buildResultList() {
    return (
      <Table striped hover responsive>
        <thead>
          <tr>
            <th>{gettext("Name")}</th>
            <th>{gettext("Can shop")}</th>
          </tr>
        </thead>
        <tbody>
          {searchResults.map((member) => (
            <tr
              key={member.id}
              onClick={() =>
                setSelectedMember(
                  selectedMember !== member ? member : undefined,
                )
              }
              className={selectedMember === member ? "table-primary" : ""}
              style={{ cursor: "pointer" }}
            >
              <td>{member.displayName}</td>
              <td>{member.canShop ? gettext("Yes") : gettext("No")}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  return buildSearchResults();
};

export default WelcomeDeskSearchResults;
