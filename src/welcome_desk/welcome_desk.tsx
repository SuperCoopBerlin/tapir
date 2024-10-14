import {createRoot} from "react-dom/client";
import TapirButton from "../components/TapirButton.tsx";

const domNode = document.getElementById('welcome_desk_button');
if (domNode) {
  const root = createRoot(domNode);
  root.render(<TapirButton variant={"warning"} text={"Button on welcome desk 22"}/>);
} else {
  console.error("SOME ERROR")
}
