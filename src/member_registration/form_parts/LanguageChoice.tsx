import { getCookie } from "../../utils/getCookie.ts";
import TapirButton from "../../components/TapirButton.tsx";

type Props = {
  language: string;
};

const languageMap: Record<string, string> = {
  de: "🇩🇪 Deutsch",
  en: "🇬🇧 English",
};

export default function LanguageChoice({ language }: Props) {
  return (
    <form
      action={
        "/i18n/setlang/?next=" +
        encodeURIComponent("/coop/member_self_registration")
      }
      method={"post"}
    >
      <input
        type={"hidden"}
        name={"csrfmiddlewaretoken"}
        value={getCookie("csrftoken")}
      />
      <input type={"hidden"} name={"language"} value={language} />
      <TapirButton variant={"outline-secondary"} text={languageMap[language]} />
    </form>
  );
}
