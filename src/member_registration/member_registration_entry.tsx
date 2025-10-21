import { createRoot } from "react-dom/client";
import MemberRegistrationCard from "./MemberRegistrationCard.tsx";

const domNode = document.getElementById("member_registration");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<MemberRegistrationCard />);
} else {
  console.error("Failed to render member registration from React");
}
