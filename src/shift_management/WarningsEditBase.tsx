import React, { useState } from "react";
import WarningsEditModal from "./WarningsEditModal.tsx";
import TapirButton from "../components/TapirButton.tsx";
import { Pencil } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

const WarningsEditBase: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <TapirButton
        variant={"outline-primary"}
        text={gettext("Edit warnings")}
        icon={Pencil}
        onClick={() => setShowModal(true)}
      />
      <WarningsEditModal show={showModal} onHide={() => setShowModal(false)} />
    </>
  );
};

export default WarningsEditBase;
