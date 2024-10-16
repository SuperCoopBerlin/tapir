import { createRoot } from "react-dom/client";
import TapirButton from "../components/TapirButton.tsx";

const domNode = document.getElementById("le_test_button");
if (domNode) {
  const root = createRoot(domNode);
  root.render(<TapirButton variant={"danger"} text={"Button on user page"} />);
} else {
  console.error("SOME ERROR");
}
