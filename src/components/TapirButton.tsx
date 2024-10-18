import React from "react";
import { Button, Spinner } from "react-bootstrap";

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
  return (
    <Button
      variant={props.variant ?? "undefined"}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        ...props.style,
      }}
      size={props.size}
      onClick={props.onClick}
      disabled={props.disabled || props.loading}
      type={props.type}
    >
      {props.icon && (props.loading ? <Spinner size="sm" /> : <props.icon />)}
      {props.text && <span>{props.loading ? "Loading..." : props.text}</span>}
    </Button>
  );
};

export default TapirButton;
