declare let gettext: (english_text: string) => string;

type Props = {
  isCompany: boolean | null;
  name: string;
  preferredName: string;
  pronouns: string;
  dob: string;
  companyName: string;
  street: string;
  postcode: string;
  city: string;
  country: string;
  email: string;
  phone: string;
};

export default function Overview({
  isCompany,
  name,
  preferredName,
  pronouns,
  dob,
  companyName,
  street,
  postcode,
  city,
  country,
  email,
  phone,
}: Props) {
  return (
    <dl>
      <div style={{ display: "flex", gap: "1ch" }}>
        <dt>{gettext("Name:")}</dt>
        <dd>{name}</dd>
      </div>
      {isCompany && (
        <>
          <div style={{ display: "flex", gap: "1ch" }}>
            <dt>{gettext("CompanyName:")}</dt>
            <dd>{companyName}</dd>
          </div>
        </>
      )}
      {!isCompany && (
        <>
          <div style={{ display: "flex", gap: "1ch" }}>
            <dt>{gettext("Preferred name:")}</dt>
            <dd>{preferredName}</dd>
          </div>
          <div style={{ display: "flex", gap: "1ch" }}>
            <dt>{gettext("Pronouns:")}</dt>
            <dd>{pronouns}</dd>
          </div>
          <div style={{ display: "flex", gap: "1ch" }}>
            <dt>{gettext("Date of birth:")}</dt>
            <dd>{new Date(dob).toLocaleDateString()}</dd>
          </div>
        </>
      )}
      <div style={{ display: "flex", gap: "1ch" }}>
        <dt>{gettext("E-mail:")}</dt>
        <dd>{email}</dd>
      </div>
      <div style={{ display: "flex", gap: "1ch" }}>
        <dt>{gettext("Phone:")}</dt>
        <dd>{phone}</dd>
      </div>
      <div style={{ display: "flex", gap: "1ch" }}>
        <dt>{gettext("Address:")}</dt>
        <dd>{[street, postcode, city, country].join(", ")}</dd>
      </div>
    </dl>
  );
}
