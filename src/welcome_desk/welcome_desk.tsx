import { createRoot } from "react-dom/client";
import WelcomeDeskSearch from "./WelcomeDeskSearch.tsx";

const domNode = document.getElementById("welcome_desk");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<WelcomeDeskSearch />);
} else {
  console.error("SOME ERROR");
}
