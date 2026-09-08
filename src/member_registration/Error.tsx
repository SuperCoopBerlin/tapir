import { XCircleFill } from "react-bootstrap-icons";
import { ReactNode } from "react";

declare let gettext: (english_text: string) => string;

type Props = {
  errorMessage: ReactNode;
};

export default function Error({ errorMessage }: Props) {
  return (
    <>
      <div
        className="mb-3"
        style={{ color: "var(--bs-danger)", fontSize: "5rem", lineHeight: 1 }}
      >
        <XCircleFill />
      </div>
      <h5>{gettext("Oops! We could not process your application :(")}</h5>
      {errorMessage}
    </>
  );
}
