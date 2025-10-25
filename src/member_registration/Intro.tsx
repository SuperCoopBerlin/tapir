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
Welcome to SuperCoop! We're excited to welcome you as a new member of our cooperative.
Please fill out the form below so we can process your application.
`)}
      </p>
    </div>
  );
}
