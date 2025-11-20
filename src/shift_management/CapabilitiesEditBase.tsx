import React, { useState } from "react";
import CapabilitiesEditModal from "./CapabilitiesEditModal.tsx";
import TapirButton from "../components/TapirButton.tsx";
import { Pencil } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const CapabilitiesEditBase: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <TapirButton
        variant={"outline-primary"}
        text={gettext("Edit qualifications")}
        icon={Pencil}
        onClick={() => setShowModal(true)}
      />
      <CapabilitiesEditModal
        show={showModal}
        onHide={() => setShowModal(false)}
      />
    </>
  );
};

export default CapabilitiesEditBase;
