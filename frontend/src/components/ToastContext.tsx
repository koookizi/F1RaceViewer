import { createContext, useCallback, useContext, useState } from "react";
import Toast from "@/components/Toast";

type ToastType = "success" | "error" | "info" | "warning";

type ToastItem = {
    id: string;
    message: string;
    type: ToastType;
};

type ToastFn = (msg: string, type?: ToastType) => void;

const ToastContext = createContext<ToastFn>(() => {});

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    const dismiss = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const showToast: ToastFn = useCallback((message, type = "info") => {
        const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

        setToasts((prev) => {
            // Optional: cap stack size (keeps UI tidy)
            const next = [...prev, { id, message, type }];
            return next.slice(-5);
        });
    }, []);

    return (
        <ToastContext.Provider value={showToast}>
            {children}

            {/* Stacking container (bottom-right). DaisyUI `toast` stacks children automatically */}
            <div className="toast toast-bottom toast-end z-50">
                {toasts.map((t) => (
                    <Toast
                        key={t.id}
                        id={t.id}
                        message={t.message}
                        type={t.type}
                        duration={8000}
                        onDismiss={dismiss}
                    />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export const useToast = () => useContext(ToastContext);
