import React, { ReactNode } from "react";
import { Modal } from "react-bootstrap";
import { ButtonVariant } from "react-bootstrap/types";
import TapirButton from "./TapirButton";

interface ConfirmDeleteModalProps {
  message: ReactNode;
  title: string;
  open: boolean;
  confirmButtonText: string;
  confirmButtonVariant: ButtonVariant;
  confirmButtonIcon: React.ComponentType;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

declare let gettext: (english_text: string) => string;

const ConfirmModal: React.FC<ConfirmDeleteModalProps> = ({
  message,
  title,
  open,
  confirmButtonText,
  confirmButtonVariant,
  confirmButtonIcon,
  onConfirm,
  onCancel,
  loading,
}) => {
  return (
    <Modal show={open} onHide={onCancel} centered={true}>
      <Modal.Header closeButton>
        <Modal.Title>
          <h5>{title}</h5>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>{message}</Modal.Body>
      <Modal.Footer
        style={{ display: "flex", justifyContent: "space-between" }}
      >
        <TapirButton
          variant="outline-secondary"
          text={gettext("Cancel")}
          onClick={onCancel}
          disabled={loading}
        />
        <TapirButton
          variant={confirmButtonVariant}
          text={confirmButtonText}
          icon={confirmButtonIcon}
          onClick={onConfirm}
          loading={loading}
        />
      </Modal.Footer>
    </Modal>
  );
};

export default ConfirmModal;
