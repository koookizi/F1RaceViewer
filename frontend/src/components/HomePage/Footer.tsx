import logo from "../../assets/logo_icon.png";

type FooterLink = { label: string; href: string };

const productLinks: FooterLink[] = [
    { label: "Telemetry", href: "/telemetry" },
    { label: "Lap times", href: "/laptimes" },
    { label: "Race positions", href: "/positions" },
    { label: "Pit stops", href: "/pitstops" },
];

const resourceLinks: FooterLink[] = [
    { label: "Docs", href: "/docs" },
    { label: "API Status", href: "/status" },
    { label: "Changelog", href: "/changelog" },
    { label: "Contact", href: "/contact" },
];

const legalLinks: FooterLink[] = [
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
    { label: "Licenses", href: "/licenses" },
];

const socialLinks: FooterLink[] = [
    { label: "GitHub", href: "https://github.com/" },
    { label: "Twitter / X", href: "https://x.com/" },
];

export function Footer() {
    return (
        <footer className="">
            <div className="border-t border-base-content/10 bg-base-100/30 backdrop-blur-md">
                <div className="mx-auto w-full max-w-7xl px-6 py-10">
                    <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
                        {/* Brand */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <img
                                    src={logo}
                                    alt="F1 Dashboard Logo"
                                    className="h-9 w-9 rounded-xl object-contain"
                                />
                                <div>
                                    <p className="text-lg font-semibold">F1 Race Viewer</p>
                                    <p className="text-sm text-base-content/60">
                                        Data tools for race weekends.
                                    </p>
                                </div>
                            </div>

                            <p className="text-sm text-base-content/60 leading-relaxed">
                                Developed by Albert Fernandez.
                                <br /> Not affiliated with Formula 1, FIA, or Liberty Media.
                            </p>
                        </div>

                        {/* Trademark & Copyright Notice */}
                        <section className="space-y-4">
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2">
                                    <h3 className="text-lg font-semibold text-error">
                                        Trademark &amp; Copyright Notice
                                    </h3>
                                </div>
                            </div>

                            <p className="text-sm text-base-content/70 leading-relaxed">
                                Formula 1®, F1®, FIA FORMULA ONE WORLD CHAMPIONSHIP™, GRAND PRIX™
                                and related marks are trademarks of Formula One Licensing B.V., a
                                Formula 1 company. All rights reserved.
                            </p>
                        </section>

                        {/* Fair Use & Educational Purpose */}
                        <section className="space-y-4">
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-semibold text-info">
                                    Fair Use &amp; Educational Purpose
                                </h3>
                            </div>

                            <p className="text-sm text-base-content/70 leading-relaxed">
                                This application is created for{" "}
                                <span className="font-semibold text-base-content">
                                    educational, analytical, and non-commercial purposes
                                </span>{" "}
                                only. The use of F1-related trademarks, logos, and imagery is
                                intended to fall under fair use provisions for:
                            </p>

                            <ul className="list-disc pl-5 text-sm text-base-content/60 space-y-2">
                                <li>Educational content and learning purposes</li>
                                <li>Statistical analysis and data visualization</li>
                                <li>Fan engagement and community discussion</li>
                            </ul>

                            <p className="text-sm text-base-content/60 italic leading-relaxed">
                                No commercial gain is derived from this application. This is an
                                independent fan project and is not affiliated with, endorsed by, or
                                connected to Formula 1, the FIA, or any F1 teams.
                            </p>
                        </section>
                    </div>

                    <div className="mt-10 flex flex-col gap-3 border-t border-base-content/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm text-base-content/60">
                            © {new Date().getFullYear()} F1 Race Viewer. All rights reserved.
                        </p>

                        <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
                            <a
                                className="link-hover text-base-content/60"
                                href="https://www.linkedin.com/in/albert-f/"
                            >
                                LinkedIn
                            </a>
                            <a
                                className="link-hover text-base-content/60"
                                href="https://github.com/koookizi"
                            >
                                Github
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </footer>
    );
}
