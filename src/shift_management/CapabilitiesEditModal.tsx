import React, { useEffect, useState } from "react";
import { Form, Modal, Spinner, Table } from "react-bootstrap";
import { useApi } from "../hooks/useApi.ts";
import { Language, ShiftsApi } from "../api-client";
import TapirButton from "../components/TapirButton.tsx";
import { Check, Floppy, PlusCircle, Trash } from "react-bootstrap-icons";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.tsx";

interface CapabilitiesEditModalProps {
  show: boolean;
  onHide: () => void;
}

interface LocalCapability {
  id?: number;
  translations: { [language: string]: string };
  shifts: string[];
}

declare let gettext: (english_text: string) => string;

const CapabilitiesEditModal: React.FC<CapabilitiesEditModalProps> = ({
  show,
  onHide,
}) => {
  const api = useApi(ShiftsApi);
  const [loading, setLoading] = useState(true);
  const [capabilities, setCapabilities] = useState<LocalCapability[]>([]);
  const [qualificationsLoading, setCapabilitiesLoading] = useState<
    Set<LocalCapability>
  >(new Set());
  const [qualificationsConfirmed, setCapabilitiesConfirmed] = useState<
    Set<LocalCapability>
  >(new Set());
  const [languages, setLanguages] = useState<Language[]>([]);
  const [
    qualificationSelectedForDeletion,
    setQualificationSelectedForDeletion,
  ] = useState<LocalCapability>();

  useEffect(() => {
    if (!show) {
      return;
    }

    setLoading(true);
    api
      .shiftsShiftUserCapabilitiesList()
      .then((capabilities) => {
        setCapabilities(
          capabilities.map((remoteCapability) => {
            return {
              id: remoteCapability.id,
              shifts: remoteCapability.shifts,
              translations: Object.fromEntries(
                remoteCapability.translations.map((translation) => [
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

  function getTranslationOrEmpty(
    capability: LocalCapability,
    language: string,
  ) {
    return capability.translations[language] ?? "";
  }

  function onDeleteCapability(capabilityToDelete: LocalCapability) {
    if (capabilityToDelete.id === undefined) {
      setCapabilities(
        capabilities.filter((capability) => capability !== capabilityToDelete),
      );
      return;
    }

    setCapabilitiesLoading((set) => addToSet(set, capabilityToDelete));

    api
      .shiftsApiShiftUserCapabilityDestroy({ id: capabilityToDelete.id })
      .then(() =>
        setCapabilities(
          capabilities.filter(
            (capability) => capability !== capabilityToDelete,
          ),
        ),
      )
      .catch(alert)
      .finally(() => {
        setCapabilitiesLoading((set) => removeFromSet(set, capabilityToDelete));
      });
  }

  function addToSet(set: Set<LocalCapability>, elementToAdd: LocalCapability) {
    set.add(elementToAdd);
    return new Set(set);
  }

  function removeFromSet(
    set: Set<LocalCapability>,
    elementToAdd: LocalCapability,
  ) {
    set.delete(elementToAdd);
    return new Set(set);
  }

  function onSaveCapability(capabilityToSave: LocalCapability) {
    setCapabilitiesLoading((set) => addToSet(set, capabilityToSave));

    if (capabilityToSave.id === undefined) {
      api
        .shiftsApiShiftUserCapabilityCreate({
          createShiftUserCapabilityRequest: {
            translations: capabilityToSave.translations,
          },
        })
        .then((capabilityId) => {
          capabilityToSave.id = capabilityId;
          setCapabilitiesConfirmed((set) => addToSet(set, capabilityToSave));
        })
        .catch(alert)
        .finally(() => {
          setCapabilitiesLoading((set) => removeFromSet(set, capabilityToSave));
        });
      return;
    }

    api
      .shiftsApiShiftUserCapabilityPartialUpdate({
        patchedUpdateShiftUserCapabilityRequest: {
          id: capabilityToSave.id,
          translations: capabilityToSave.translations,
        },
      })
      .then(() => {
        setCapabilitiesConfirmed((set) => addToSet(set, capabilityToSave));
      })
      .finally(() => {
        setCapabilitiesLoading((set) => removeFromSet(set, capabilityToSave));
      });
  }

  function getDeleteConfirmationMessage(capability: LocalCapability) {
    const translations = Object.values(capability.translations);
    const name = translations.length > 0 ? translations[0] : gettext("no name");

    return (
      <>
        <p>
          {gettext(
            "Are you sure you want to delete the following qualification: ",
          )}
          {name}
          {"?"}
        </p>
        {capability.shifts.length === 0 ? (
          <p>{gettext("This qualification is not used in any slot.")}</p>
        ) : (
          <>
            <p>
              {gettext("This qualification is used in the following slots: ")}
            </p>
            <ul>
              {capability.shifts.map((shift) => (
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
        show={show && qualificationSelectedForDeletion === undefined}
        onHide={onHide}
        size={"lg"}
      >
        <Modal.Header closeButton>
          <h5>{gettext("Edit qualifications")}</h5>
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
                {capabilities.map((qualification) => (
                  <tr key={qualification.id}>
                    {languages.map((language) => (
                      <td key={qualification.id + "_" + language.shortName}>
                        <Form.Control
                          value={getTranslationOrEmpty(
                            qualification,
                            language.shortName,
                          )}
                          placeholder={language.displayName}
                          onChange={(event) => {
                            qualification.translations[language.shortName] =
                              event.target.value;
                            setCapabilities([...capabilities]);
                            setCapabilitiesConfirmed((set) =>
                              removeFromSet(set, qualification),
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
                          onClick={() =>
                            setQualificationSelectedForDeletion(qualification)
                          }
                          loading={qualificationsLoading.has(qualification)}
                        />
                        <TapirButton
                          variant={
                            qualificationsConfirmed.has(qualification)
                              ? "success"
                              : "primary"
                          }
                          icon={
                            qualificationsConfirmed.has(qualification)
                              ? Check
                              : Floppy
                          }
                          onClick={() => onSaveCapability(qualification)}
                          loading={qualificationsLoading.has(qualification)}
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
                      text={gettext("Add a qualification")}
                      icon={PlusCircle}
                      onClick={() =>
                        setCapabilities([
                          ...capabilities,
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
      {qualificationSelectedForDeletion && (
        <ConfirmDeleteModal
          message={getDeleteConfirmationMessage(
            qualificationSelectedForDeletion,
          )}
          open={true}
          onConfirm={() => {
            onDeleteCapability(qualificationSelectedForDeletion);
            setQualificationSelectedForDeletion(undefined);
          }}
          onCancel={() => setQualificationSelectedForDeletion(undefined)}
        />
      )}
    </>
  );
};

export default CapabilitiesEditModal;
