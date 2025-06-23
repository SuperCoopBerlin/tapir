import React, { useEffect, useState } from "react";
import { Form, Modal, Spinner, Table } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { Language, ShiftsApi } from "../api-client";
import TapirButton from "../components/TapirButton.tsx";
import { Floppy, PlusCircle, Trash } from "react-bootstrap-icons";

interface WarningsEditModalProps {
  show: boolean;
  onHide: () => void;
}

interface LocalWarning {
  id?: number;
  translations: { [language: string]: string };
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
  const [languages, setLanguages] = useState<Language[]>([]);

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

    setWarningsLoading((set) => {
      set.add(warningToDelete);
      return set;
    });

    api
      .shiftsApiShiftSlotWarningDestroy({ id: warningToDelete.id })
      .then(() =>
        setWarnings(warnings.filter((warning) => warning !== warningToDelete)),
      )
      .catch(alert)
      .finally(() => {
        setWarningsLoading((set) => {
          set.delete(warningToDelete);
          return set;
        });
      });
  }

  function onSaveWarning(warningToSave: LocalWarning) {
    setWarningsLoading((set) => {
      set.add(warningToSave);
      return set;
    });

    if (warningToSave.id === undefined) {
      api
        .shiftsApiShiftSlotWarningCreate({
          createShiftSlotWarningRequest: {
            translations: warningToSave.translations,
          },
        })
        .then((warningId) => (warningToSave.id = warningId))
        .catch(alert)
        .finally(() => {
          setWarningsLoading((set) => {
            set.delete(warningToSave);
            return set;
          });
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
      .finally(() => {
        setWarningsLoading((set) => {
          set.delete(warningToSave);
          return set;
        });
      });
  }

  return (
    <Modal show={show} onHide={onHide} size={"lg"}>
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
                        onClick={() => onDeleteWarning(warning)}
                        loading={warningsLoading.has(warning)}
                      />
                      <TapirButton
                        variant={"primary"}
                        icon={Floppy}
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
                        { id: undefined, translations: {} },
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
  );
};

export default WarningsEditModal;
