import React, { useEffect, useState } from "react";
import { Alert, Card, Form, Spinner, Table } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import {
  FetchError,
  ShareOwnerForWelcomeDesk,
  WelcomedeskApi,
} from "../api-client";

declare let gettext: (english_text: string) => string;

const WelcomeDeskSearch: React.FC = () => {
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<
    ShareOwnerForWelcomeDesk[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [controller, setController] = useState<AbortController | null>(null);
  const [selectedMember, setSelectedMember] =
    useState<ShareOwnerForWelcomeDesk | null>(null);
  const api = useApi(WelcomedeskApi);

  useEffect(() => {
    updateSearchResults();
  }, [searchInput]);

  function resetSearchResults() {
    setSearchResults([]);
    setLoading(false);
    setError("");
    setSelectedMember(null);
  }

  function buildErrorMessage(searchInput: string) {
    return (
      gettext(
        "Whoops! Something went wrong. Please try again. If it keeps happening, please write in the #tapir channel on Slack with your current search: ",
      ) +
      "'" +
      searchInput +
      "'"
    );
  }

  function updateSearchResults() {
    if (controller) controller.abort();

    if (!searchInput) {
      resetSearchResults();
      return;
    }

    const localController = new AbortController();
    setController(localController);
    setLoading(true);
    setError("");
    setSelectedMember(null);

    api
      .welcomedeskApiSearchList(
        { searchInput: searchInput },
        { signal: localController.signal },
      )
      .then((results) => {
        setSearchResults(results);
        if (results.length === 1) {
          setSelectedMember(results[0]);
        }
        setLoading(false);
      })
      .catch((error: FetchError) => {
        if (error.cause && error.cause.name === "AbortError") return;
        setError(buildErrorMessage(searchInput));
        console.log(error);
        setLoading(false);
      });
  }

  function getCardContent() {
    if (!searchInput) {
      return (
        <Alert variant={"primary"}>
          {gettext("Use the search field on the top right.")}
        </Alert>
      );
    }

    if (loading) return <Spinner />;

    if (error) return <Alert variant={"danger"}>{error}</Alert>;

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
                setSelectedMember(selectedMember !== member ? member : null)
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

  function getDetailCardColor(member: ShareOwnerForWelcomeDesk) {
    if (!member.canShop) return "danger";
    if (member.warnings.length > 0) return "warning";
    return "success";
  }

  return (
    <div className={"card-group"}>
      <Card>
        <Card.Header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h5>{gettext("Welcome Desk")}</h5>
          <Form.Group>
            <Form.Control
              placeholder={gettext("Name or member ID")}
              onChange={(changeEvent) =>
                setSearchInput(changeEvent.target.value)
              }
            />
          </Form.Group>
        </Card.Header>
        <Card.Body>{getCardContent()}</Card.Body>
      </Card>
      {selectedMember !== null && (
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
      )}
    </div>
  );
};

export default WelcomeDeskSearch;
