import React, { useEffect, useState } from "react";
import { Form, Modal, Spinner, Table } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { Language, ShiftsApi } from "../api-client";
import TapirButton from "../components/TapirButton.tsx";
import { Check, Floppy, PlusCircle, Trash } from "react-bootstrap-icons";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.tsx";

interface WarningsEditModalProps {
  show: boolean;
  onHide: () => void;
}

interface LocalWarning {
  id?: number;
  translations: { [language: string]: string };
  shifts: string[];
}

declare let gettext: (english_text: string) => string;

const WarningsEditModal: React.FC<WarningsEditModalProps> = ({
  show,
  onHide,
}) => {
  const api = useApi(ShiftsApi);
  const [loading, setLoading] = useState(true);
  const [warnings, setWarnings] = useState<LocalWarning[]>([]);
  const [warningsLoading, setWarningsLoading] = useState<Set<LocalWarning>>(
    new Set(),
  );
  const [warningsConfirmed, setWarningsConfirmed] = useState<Set<LocalWarning>>(
    new Set(),
  );
  const [languages, setLanguages] = useState<Language[]>([]);
  const [warningSelectedForDeletion, setWarningSelectedForDeletion] =
    useState<LocalWarning>();

  useEffect(() => {
    if (!show) {
      return;
    }

    setLoading(true);
    api
      .shiftsShiftSlotWarningsList()
      .then((warnings) => {
        setWarnings(
          warnings.map((remoteWarning) => {
            return {
              id: remoteWarning.id,
              shifts: remoteWarning.shifts,
              translations: Object.fromEntries(
                remoteWarning.translations.map((translation) => [
                  translation.language,
                  translation.name,
                ]),
              ),
            };
          }),
        );
      })
      .catch(alert)
      .finally(() => setLoading(false));

    api.shiftsApiLanguagesList().then(setLanguages).catch(alert);
  }, [show]);

  function getTranslationOrEmpty(warning: LocalWarning, language: string) {
    return warning.translations[language] ?? "";
  }

  function onDeleteWarning(warningToDelete: LocalWarning) {
    if (warningToDelete.id === undefined) {
      setWarnings(warnings.filter((warning) => warning !== warningToDelete));
      return;
    }

    setWarningsLoading((set) => addToSet(set, warningToDelete));

    api
      .shiftsApiShiftSlotWarningDestroy({ id: warningToDelete.id })
      .then(() =>
        setWarnings(warnings.filter((warning) => warning !== warningToDelete)),
      )
      .catch(alert)
      .finally(() => {
        setWarningsLoading((set) => removeFromSet(set, warningToDelete));
      });
  }

  function addToSet(set: Set<LocalWarning>, elementToAdd: LocalWarning) {
    set.add(elementToAdd);
    return new Set(set);
  }

  function removeFromSet(set: Set<LocalWarning>, elementToAdd: LocalWarning) {
    set.delete(elementToAdd);
    return new Set(set);
  }

  function onSaveWarning(warningToSave: LocalWarning) {
    setWarningsLoading((set) => addToSet(set, warningToSave));

    if (warningToSave.id === undefined) {
      api
        .shiftsApiShiftSlotWarningCreate({
          createShiftSlotWarningRequest: {
            translations: warningToSave.translations,
          },
        })
        .then((warningId) => {
          warningToSave.id = warningId;
          setWarningsConfirmed((set) => addToSet(set, warningToSave));
        })
        .catch(alert)
        .finally(() => {
          setWarningsLoading((set) => removeFromSet(set, warningToSave));
        });
      return;
    }

    api
      .shiftsApiShiftSlotWarningPartialUpdate({
        patchedUpdateShiftSlotWarningRequest: {
          id: warningToSave.id,
          translations: warningToSave.translations,
        },
      })
      .then(() => {
        setWarningsConfirmed((set) => addToSet(set, warningToSave));
      })
      .finally(() => {
        setWarningsLoading((set) => removeFromSet(set, warningToSave));
      });
  }

  function getDeleteConfirmationMessage(warning: LocalWarning) {
    const translations = Object.values(warning.translations);
    const name = translations.length > 0 ? translations[0] : gettext("no name");

    return (
      <>
        <p>
          {gettext("Are you sure you want to delete the following warning: ")}
          {name}
          {"?"}
        </p>
        {warning.shifts.length === 0 ? (
          <p>{gettext("This warning is not used in any slot.")}</p>
        ) : (
          <>
            <p>{gettext("This warning is used in the following slots: ")}</p>
            <ul>
              {warning.shifts.map((shift) => (
                <li>{shift}</li>
              ))}
            </ul>
          </>
        )}
      </>
    );
  }

  return (
    <>
      <Modal
        show={show && warningSelectedForDeletion === undefined}
        onHide={onHide}
        size={"lg"}
      >
        <Modal.Header closeButton>
          <h5>{gettext("Edit shift warnings")}</h5>
        </Modal.Header>
        <Modal.Body>
          {loading ? (
            <Spinner />
          ) : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  {languages.map((language) => (
                    <th key={language.shortName}>{language.displayName}</th>
                  ))}
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {warnings.map((warning) => (
                  <tr key={warning.id}>
                    {languages.map((language) => (
                      <td key={warning.id + "_" + language.shortName}>
                        <Form.Control
                          value={getTranslationOrEmpty(
                            warning,
                            language.shortName,
                          )}
                          placeholder={language.displayName}
                          onChange={(event) => {
                            warning.translations[language.shortName] =
                              event.target.value;
                            setWarnings([...warnings]);
                            setWarningsConfirmed((set) =>
                              removeFromSet(set, warning),
                            );
                          }}
                        />
                      </td>
                    ))}
                    <td>
                      <div
                        className={"d-flex flex-row gap-2 align-items-center"}
                        style={{ height: "100%" }}
                      >
                        <TapirButton
                          variant={"outline-danger"}
                          icon={Trash}
                          onClick={() => setWarningSelectedForDeletion(warning)}
                          loading={warningsLoading.has(warning)}
                        />
                        <TapirButton
                          variant={
                            warningsConfirmed.has(warning)
                              ? "success"
                              : "primary"
                          }
                          icon={warningsConfirmed.has(warning) ? Check : Floppy}
                          onClick={() => onSaveWarning(warning)}
                          loading={warningsLoading.has(warning)}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={4}>
                    <TapirButton
                      variant={"outline-primary"}
                      text={gettext("Add a warning")}
                      icon={PlusCircle}
                      onClick={() =>
                        setWarnings([
                          ...warnings,
                          { id: undefined, translations: {}, shifts: [] },
                        ])
                      }
                    />
                  </td>
                </tr>
              </tfoot>
            </Table>
          )}
        </Modal.Body>
      </Modal>
      {warningSelectedForDeletion && (
        <ConfirmDeleteModal
          message={getDeleteConfirmationMessage(warningSelectedForDeletion)}
          open={true}
          onConfirm={() => {
            onDeleteWarning(warningSelectedForDeletion);
            setWarningSelectedForDeletion(undefined);
          }}
          onCancel={() => setWarningSelectedForDeletion(undefined)}
        />
      )}
    </>
  );
};

export default WarningsEditModal;
