import { createRoot } from "react-dom/client";
import FancyGraphCard from "./FancyGraphCard.tsx";

const domNode = document.getElementById("fancy_graph");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<FancyGraphCard />);
} else {
  console.error("Failed to render welcome desk from React");
}
