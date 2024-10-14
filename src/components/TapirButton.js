"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = require("react");
const TapirButton = (props) => {
    var _a;
    return (<button className={(_a = props.variant) !== null && _a !== void 0 ? _a : "undefined"} style={Object.assign({ display: "flex", alignItems: "center", gap: "6px", height: "100%" }, props.style)} onClick={props.onClick} disabled={props.disabled || props.loading} type={props.type}>
      {props.icon && (props.loading ? <span>LOADING_ICON</span> : <props.icon />)}
      {props.text && <span>{props.loading ? "Loading..." : props.text}</span>}
    </button>);
};
exports.default = TapirButton;
//# sourceMappingURL=TapirButton.js.map