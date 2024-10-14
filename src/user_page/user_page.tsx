import {createRoot} from "react-dom/client";
import TapirButton from "../components/TapirButton.tsx";

const domNode = document.getElementById('navigation');
if (domNode) {
  const root = createRoot(domNode);
  root.render(<TapirButton variant={"danger"} />);
} else {
  console.error("SOME ERROR")
}
