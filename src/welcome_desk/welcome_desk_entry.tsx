import { createRoot } from "react-dom/client";
import WelcomeDeskCard from "./WelcomeDeskCard.tsx";

const domNode = document.getElementById("welcome_desk");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<WelcomeDeskCard />);
} else {
  console.error("Failed to render welcome desk from React");
}
