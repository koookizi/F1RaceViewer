import { useEffect, useState } from "react";

type ToastType = "success" | "error" | "info" | "warning";

interface ToastProps {
    id: string;
    message: string;
    type?: ToastType;
    duration?: number; // ms
    onDismiss: (id: string) => void;
}

const typeClasses: Record<ToastType, string> = {
    success: "alert-success",
    error: "alert-error",
    info: "alert-info",
    warning: "alert-warning",
};

export default function Toast({
    id,
    message,
    type = "info",
    duration = 8000,
    onDismiss,
}: ToastProps) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        // enter animation (next tick)
        const raf = requestAnimationFrame(() => setVisible(true));

        // start leaving a bit before removal so fade-out can play
        const leaveMs = Math.max(0, duration - 250);
        const t1 = window.setTimeout(() => setVisible(false), leaveMs);

        // remove after duration
        const t2 = window.setTimeout(() => onDismiss(id), duration);

        return () => {
            cancelAnimationFrame(raf);
            window.clearTimeout(t1);
            window.clearTimeout(t2);
        };
    }, [id, duration, onDismiss]);

    return (
        <div
            className={[
                "alert shadow-lg",
                typeClasses[type],
                "cursor-pointer select-none",
                "transition-all duration-200 ease-out",
                visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2",
            ].join(" ")}
            onClick={() => onDismiss(id)}
            role="status"
        >
            <span className="text-lg">
                {type === "success" && "✅"}
                {type === "error" && "❌"}
                {type === "warning" && "⚠️"}
                {type === "info" && "ℹ️"}
            </span>
            <span>{message}</span>
        </div>
    );
}
