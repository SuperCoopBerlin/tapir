import { createRoot } from "react-dom/client";
import WarningsEditBase from "./WarningsEditBase.tsx";
import CapabilitiesEditBase from "./CapabilitiesEditBase.tsx";

const warningsElement = document.getElementById("warnings");
if (warningsElement) {
  const root = createRoot(warningsElement);
  root.render(<WarningsEditBase />);
} else {
  console.error("Failed to render warnings from React");
}

const qualificationsElement = document.getElementById("qualifications");
if (qualificationsElement) {
  const root = createRoot(qualificationsElement);
  root.render(<CapabilitiesEditBase />);
} else {
  console.error("Failed to render qualifications from React");
}
