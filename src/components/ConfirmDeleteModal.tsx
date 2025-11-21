import React, { ReactNode } from "react";
import ConfirmModal from "./ConfirmModal";
import { Trash } from "react-bootstrap-icons";

interface ConfirmDeleteModalProps {
  message: ReactNode;
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

declare let gettext: (english_text: string) => string;

const ConfirmDeleteModal: React.FC<ConfirmDeleteModalProps> = ({
  message,
  open,
  onConfirm,
  onCancel,
  loading,
}) => {
  return (
    <ConfirmModal
      message={message}
      title={gettext("Confirm deletion")}
      open={open}
      confirmButtonText={gettext("Delete")}
      confirmButtonIcon={Trash}
      confirmButtonVariant="danger"
      onConfirm={onConfirm}
      onCancel={onCancel}
      loading={loading}
    />
  );
};

export default ConfirmDeleteModal;
