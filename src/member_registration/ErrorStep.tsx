import { XCircleFill } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

type Props = {
  errorMessage: string;
};

export default function ErrorStep({ errorMessage }: Props) {
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
