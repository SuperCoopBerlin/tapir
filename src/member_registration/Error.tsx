import { XCircleFill } from "react-bootstrap-icons";
import { EMAIL_ADDRESS_MEMBER_OFFICE } from "./constants";

declare let gettext: (english_text: string) => string;

export default function Error() {
  return (
    <>
      <div
        className="mb-3"
        style={{ color: "var(--bs-danger)", fontSize: "5rem", lineHeight: 1 }}
      >
        <XCircleFill />
      </div>
      <h5>{gettext("Oops! We could not process your application :(")}</h5>
      <p style={{ width: "100%", maxWidth: "700px" }}>
        {gettext(
          `Please try again later. If you keep having issues, please contact the Members Office at`,
        )}{" "}
        <a href={`mailto:${EMAIL_ADDRESS_MEMBER_OFFICE}`}>
          {EMAIL_ADDRESS_MEMBER_OFFICE}
        </a>
      </p>
    </>
  );
}
