type ToastType = "success" | "error" | "info" | "warning";

interface ToastProps {
    message: string;
    type?: ToastType;
}

const typeClasses: Record<ToastType, string> = {
    success: "alert-success",
    error: "alert-error",
    info: "alert-info",
    warning: "alert-warning",
};

export default function Toast({ message, type = "info" }: ToastProps) {
    return (
        <div className="toast toast-bottom toast-end z-50">
            <div className={`alert ${typeClasses[type]}`}>
                {type === "success" && "✅"}
                {type === "error" && "❌"}
                <span>{message}</span>
            </div>
        </div>
    );
}
