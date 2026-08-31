import { CheckCircleFill } from "react-bootstrap-icons";

declare let gettext: (english_text: string) => string;

type Props = {
  name: string;
  emailAddressMemberOffice: string;
};

export default function Success({ name, emailAddressMemberOffice }: Props) {
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
        <a href={`mailto:${emailAddressMemberOffice}`}>
          {emailAddressMemberOffice}
        </a>
      </p>
    </>
  );
}
