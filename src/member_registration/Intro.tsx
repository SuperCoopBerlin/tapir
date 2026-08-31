import LanguageChoice from "./form_parts/LanguageChoice.tsx";

declare let gettext: (english_text: string) => string;

export default function Intro() {
  return (
    <div className="mb-4" style={{ width: "100%", maxWidth: "700px" }}>
      <p>
        <img
          style={{ width: "100%" }}
          src="https://supercoop.de/wp-content/uploads/supercoop-header.jpg"
        />
      </p>
      <p>
        {gettext(`
As a member of SuperCoop, you can buy regional and healthy food, 
be part of our active community and have a say in all decisions. 
The co-op is a vibrant marketplace. 
You support day-to-day operations (or other working groups) by putting in three hours’ work per month 
alongside other members in a great atmosphere.
In working groups, you can champion the issues that matter to you 
and play an active role in shaping the future of the co-op.
`)}
      </p>
      <div className={"d-flex gap-2"}>
        <LanguageChoice language={"de"} />
        <LanguageChoice language={"en"} />
      </div>
      <hr />
    </div>
  );
}
