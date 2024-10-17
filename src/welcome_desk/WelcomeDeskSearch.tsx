import React, { useEffect, useState } from "react";
import { Alert, Card, Form, Spinner } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import {
  FetchError,
  ShareOwnerForWelcomeDesk,
  WelcomedeskApi,
} from "../api-client";

const WelcomeDeskSearch: React.FC = () => {
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<
    ShareOwnerForWelcomeDesk[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [controller, setController] = useState<AbortController | null>(null);
  const api = useApi(WelcomedeskApi);

  useEffect(() => {
    updateSearchResults();
  }, [searchInput]);

  function resetSearchResults() {
    setSearchResults([]);
    setLoading(false);
    setError("");
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

    api
      .welcomedeskApiSearchList(
        { searchInput: searchInput },
        { signal: localController.signal },
      )
      .then((results) => {
        setSearchResults(results);
        setLoading(false);
      })
      .catch((error: FetchError) => {
        if (error.cause && error.cause.name === "AbortError") return;
        setError(
          "Whoops! Something went wrong. Please try again. If it keeps happening, please write in the #tapir channel on Slack with your current search: '" +
            searchInput +
            "'",
        );
        console.log(error);
        setLoading(false);
      });
  }

  function getCardContent() {
    if (!searchInput) {
      return (
        <Alert variant={"primary"}>
          Use the search field on the top right.
        </Alert>
      );
    }

    if (loading) return <Spinner />;

    if (error) return <Alert variant={"danger"}>{error}</Alert>;

    return buildResultList();
  }

  function buildResultList() {
    return (
      <ul>
        {searchResults.map((member) => (
          <li key={member.id}>
            {member.id} - {member.displayName} -{" "}
            {member.canShop ? "Can shop" : "Cannot shop"}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <>
      <Card>
        <Card.Header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h5>Welcome Desk</h5>
          <Form.Group>
            <Form.Control
              placeholder={"Name or member ID"}
              onChange={(changeEvent) =>
                setSearchInput(changeEvent.target.value)
              }
            />
          </Form.Group>
        </Card.Header>
        <Card.Body>{getCardContent()}</Card.Body>
      </Card>
    </>
  );
};

export default WelcomeDeskSearch;
