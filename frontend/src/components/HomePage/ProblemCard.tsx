import { type ReactNode } from "react";

interface ProblemCardProps {
    icon: ReactNode;
    title: string;
    description: string;
}

export function ProblemCard({ icon, title, description }: ProblemCardProps) {
    return (
        <div
            className="
                group relative
                bg-base-100/90 backdrop-blur-md
                border border-base-content/10
                rounded-2xl p-6
                shadow-md
                transition-all duration-300
                hover:-translate-y-1
                hover:border-error/40
                hover:shadow-[0_0_25px_rgba(0,0,0,0.25)]
                text-center
            "
        >
            {/* Gradient glow on hover */}
            <div
                className="
                    absolute inset-0 rounded-2xl
                    opacity-0 group-hover:opacity-100
                    transition duration-300
                    bg-gradient-to-br from-error/10 to-transparent
                    pointer-events-none
                "
            />

            <div className="relative z-10">
                <div className="text-3xl mb-4">{icon}</div>

                <h2 className="text-lg font-semibold mb-3">{title}</h2>

                <p className="text-base-content/60 leading-relaxed">{description}</p>
            </div>
        </div>
    );
}
