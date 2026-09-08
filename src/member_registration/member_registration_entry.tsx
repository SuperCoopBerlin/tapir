import { createRoot } from "react-dom/client";
import MemberRegistration from "./MemberRegistration.tsx";

const domNode = document.getElementById("member_registration");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<MemberRegistration />);
} else {
  console.error("Failed to render member registration from React");
}
