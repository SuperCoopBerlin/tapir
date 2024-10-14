import React from "react";

interface TapirButtonProps {
  variant: string;
  text?: string;
  icon?: React.ComponentType;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  size?: "sm" | "lg" | undefined;
  style?: React.CSSProperties;
  loading?: boolean;
  type?: "submit" | "reset" | "button" | undefined;
}

const TapirButton: React.FC<TapirButtonProps> = (props) => {
  const className = "btn tapir-btn btn-"+props.variant;
  return (
    <button
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        height: "100%",
        ...props.style,
      }}
      onClick={props.onClick}
      disabled={props.disabled || props.loading}
      type={props.type}
    >
      {props.icon && (props.loading ? <span>LOADING_ICON</span> : <props.icon />)}
      {props.text && <span>{props.loading ? "Loading..." : props.text}</span>}
    </button>
  );
};

export default TapirButton;
