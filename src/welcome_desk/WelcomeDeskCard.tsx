import React, { useEffect, useState } from "react";
import { Card, Form } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import {
  FetchError,
  ShareOwnerForWelcomeDesk,
  WelcomedeskApi,
} from "../api-client";
import WelcomeDeskSearchResults from "./WelcomeDeskSearchResults.tsx";
import WelcomeDeskMemberDetails from "./WelcomeDeskMemberDetails.tsx";

declare let gettext: (english_text: string) => string;

const WelcomeDeskCard: React.FC = () => {
  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<
    ShareOwnerForWelcomeDesk[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [controller, setController] = useState<AbortController>();
  const [selectedMember, setSelectedMember] =
    useState<ShareOwnerForWelcomeDesk>();
  const api = useApi(WelcomedeskApi);

  useEffect(() => {
    updateSearchResults();
  }, [searchInput]);

  function resetSearchResults() {
    setSearchResults([]);
    setLoading(false);
    setError("");
    setSelectedMember(undefined);
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
    setSelectedMember(undefined);

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
        <Card.Body>
          <WelcomeDeskSearchResults
            searchResults={searchResults}
            error={error}
            setSelectedMember={setSelectedMember}
            selectedMember={selectedMember}
            loading={loading}
          />
        </Card.Body>
      </Card>
      {selectedMember && (
        <WelcomeDeskMemberDetails selectedMember={selectedMember} />
      )}
    </div>
  );
};

export default WelcomeDeskCard;
