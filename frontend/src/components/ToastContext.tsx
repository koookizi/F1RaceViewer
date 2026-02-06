import { createContext, useContext, useState } from "react";
import Toast from "@/components/Toast";

type ToastType = "success" | "error" | "info" | "warning";

interface ToastState {
    message: string;
    type: ToastType;
}

const ToastContext = createContext<(msg: string, type?: ToastType) => void>(
    () => {}
);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toast, setToast] = useState<ToastState | null>(null);

    const showToast = (message: string, type: ToastType = "info") => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    return (
        <ToastContext.Provider value={showToast}>
            {children}
            {toast && <Toast message={toast.message} type={toast.type} />}
        </ToastContext.Provider>
    );
}

export const useToast = () => useContext(ToastContext);
