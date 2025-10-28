import { CheckCircleFill } from "react-bootstrap-icons";
import { EMAIL_ADDRESS_MEMBER_OFFICE } from "./constants";

declare let gettext: (english_text: string) => string;

type Props = {
  name: string;
};

export default function Success({ name }: Props) {
  return (
    <>
      <div
        className="mb-3"
        style={{ color: "var(--bs-success)", fontSize: "5rem", lineHeight: 1 }}
      >
        <CheckCircleFill />
      </div>
      <h5>
        {gettext("Thank you for joining")}, {name} {"<3"}
      </h5>
      <p style={{ width: "100%", maxWidth: "700px" }}>
        {gettext(
          `We have received your application and will let you know via e-mail once it has been processed.
          Should you have any questions about your membership, please write to`,
        )}{" "}
        <a href={`mailto:${EMAIL_ADDRESS_MEMBER_OFFICE}`}>
          {EMAIL_ADDRESS_MEMBER_OFFICE}
        </a>
      </p>
    </>
  );
}
