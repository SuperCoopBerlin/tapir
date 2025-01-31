import {createRoot} from "react-dom/client";
import FancyExportCard from "./FancyExportCard.tsx";

const domNode = document.getElementById("fancy_export");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<FancyExportCard />);
} else {
  console.error("Failed to render fancy export from React");
}
