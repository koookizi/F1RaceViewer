import { type ReactNode } from "react";

interface FeatureCardProps {
    icon: ReactNode;
    title: string;
    description: string;
}

export function FeatureCard({ icon, title, description }: FeatureCardProps) {
    return (
        <div
            className="
        group
        relative
        bg-base-100/90
        backdrop-blur-md
        border border-base-content/10
        rounded-2xl
        p-6
        shadow-md
        transition-all duration-300
        hover:-translate-y-1
        hover:border-primary/40
        hover:shadow-[0_0_25px_rgba(0,0,0,0.25)]
      "
        >
            <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition duration-300 bg-linear-to-br from-primary/10 to-transparent pointer-events-none" />

            <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                    <div className="text-2xl">{icon}</div>
                    <h2 className="text-lg font-semibold">{title}</h2>
                </div>

                <p className="text-base-content/60 leading-relaxed text-start">{description}</p>
            </div>
        </div>
    );
}
