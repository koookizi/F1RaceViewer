type AlertProps = {
  text: string;
  type?: "success" | "warning" | "info" | "error";
};

export function Alert({ text, type = "error" }: AlertProps) {
  return (
    <div role="alert" className={`alert alert-${type}`}>
      <span>{text}</span>
    </div>
  );
}
