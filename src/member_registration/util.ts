import { PreferredLanguage } from "./constants";

export const getNavigatorLanguage = () => {
  const lang = navigator.language.split("-").at(0)?.toLowerCase();
  switch (lang) {
    case "en":
      return PreferredLanguage.ENGLISH;
    default:
      return PreferredLanguage.GERMAN;
  }
};
