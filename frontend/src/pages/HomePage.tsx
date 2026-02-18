import { Link } from "react-router-dom";
import hero_bg from "../assets/hero-bg.jpg";
import logo from "../assets/logo.png";
import { FeatureCard } from "../components/HomePage/FeatureCard";
import { Footer } from "../components/HomePage/Footer";
import report_mockup from "../assets/generate_reports_mockup.png";
import race_viewer_preview from "../assets/race_viewer_preview.mp4";
import { ProblemCard } from "@/components/HomePage/ProblemCard";
import call_bg from "@/assets/race-control-room-stockcake.webp";

export function HomePage() {
    return (
        <div className="min-h-screen bg-base-200 flex flex-col">
            {/* Navbar */}
            <div className="navbar bg-base-100 shadow-sm px-6">
                <div className="flex-1">
                    <img
                        src={logo}
                        alt="F1 Race Viewer"
                        className="h-8 w-auto px-4 object-contain"
                    />
                </div>
                <div className="flex-none">
                    <Link to="/race-viewer" className="btn btn-primary btn-sm">
                        Enter Dashboard
                    </Link>
                </div>
            </div>

            {/* Hero with Background Image */}
            <div
                className="hero h-[600px] relative"
                style={{
                    backgroundImage: `url("${hero_bg}")`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                }}
            >
                {/* Dark overlay */}
                <div className="absolute inset-0 bg-linear-to-r from-black/90 via-black/70 to-black/90"></div>

                <div className="hero-content text-center text-neutral-content relative z-10">
                    <div className="max-w-2xl">
                        <div className="flex justify-center items-center">
                            <img
                                src={logo}
                                alt="F1 Race Viewer"
                                className="h-12 w-auto px-4 object-contain mb-8"
                            />
                        </div>
                        <h1 className="text-5xl md:text-7xl font-bold">Explore Formula 1 Data</h1>
                        <p className="py-6 text- md:text-lg">
                            Visualise race sessions, compare drivers, analyse teams, and dive into
                            historical F1 statistics all in one place.
                        </p>
                        <Link to="/race-viewer" className="btn btn-primary">
                            Start Exploring
                        </Link>
                    </div>
                </div>
            </div>

            <div className="w-full px-6 md:px-35 ">
                {/* What The Tool Does */}
                <section className="py-16 text-center">
                    <div className="mx-auto max-w-6xl">
                        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-base-content">
                            Where Race Data Comes Alive.
                        </h1>
                        <p className="mt-6 text-lg text-base-content/60 max-w-2xl mx-auto">
                            Analyze millions of F1 data points from the beginning of the sport.
                        </p>
                        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                            <FeatureCard
                                icon="📈"
                                title="Generate Reports"
                                description="Turn race data into clear, interactive performance insights."
                            />

                            <FeatureCard
                                icon="🏁"
                                title="Race Playback"
                                description="Relive races lap-by-lap with dynamic leaderboard updates."
                            />

                            <FeatureCard
                                icon="👤"
                                title="Driver Analysis"
                                description="Explore complete career stats and season performance trends."
                            />

                            <FeatureCard
                                icon="🏎️"
                                title="Constructor Analysis"
                                description="Compare team performance, reliability, and historical success."
                            />
                        </div>
                    </div>
                </section>

                {/* Report Generation */}
                <section className="-mx-6 md:-mx-35 px-6 md:px-35 py-16 text-center bg-base-100">
                    <div className="mx-auto max-w-6xl text-center">
                        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-base-content">
                            Lights Out. Data On.
                        </h1>

                        <p className="mt-6 text-lg text-base-content/60 max-w-2xl mx-auto">
                            Explore Formula 1 performance through interactive reports, race
                            playback, and deep historical analysis instantly.
                        </p>

                        <div className="mt-20 grid gap-14 md:grid-cols-3">
                            <Step
                                number="1"
                                title="Find your subject"
                                description="Pick a driver, constructor, or race."
                            />
                            <Step
                                number="2"
                                title="Select your template"
                                description="Choose from a range of pre-built templates."
                            />
                            <Step
                                number="3"
                                title="Export your report"
                                description="Download your report in PDF or CSV format."
                            />
                        </div>

                        <div className="mt-8 relative flex justify-center items-center">
                            {/* Image */}
                            <img
                                src={report_mockup}
                                alt="Report preview"
                                className="max-h-[800px] w-auto object-contain md:px-30"
                            />

                            {/* Bottom fade */}
                            <div className="pointer-events-none absolute bottom-0 left-0 w-full h-80 bg-linear-to-b from-transparent to-base-100" />
                        </div>
                    </div>
                </section>

                {/* Race Viewer */}
                <section className="py-16">
                    <div className="mx-auto max-w-6xl flex flex-col md:flex-row items-center justify-center gap-30">
                        {/* Video */}
                        <div className="flex-1 flex justify-center">
                            <div className="hover-3d">
                                <figure className="rounded-2xl overflow-hidden shadow-xl">
                                    <video
                                        src={race_viewer_preview}
                                        autoPlay
                                        loop
                                        muted
                                        playsInline
                                        className="w-full h-auto object-contain"
                                    />
                                </figure>

                                {/* 8 empty divs */}
                                <div></div>
                                <div></div>
                                <div></div>
                                <div></div>
                                <div></div>
                                <div></div>
                                <div></div>
                                <div></div>
                            </div>
                        </div>

                        {/* Text */}
                        <div className="flex-1 max-w-xl text-center md:text-left">
                            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-base-content">
                                Relive the Race.
                            </h1>

                            <p className="mt-6 text-lg text-base-content/60">
                                Watch every lap unfold with live position changes, decisive
                                overtakes, and race-defining moments, reconstructed in real time.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Problem */}
                <section className="-mx-6 md:-mx-35 px-6 md:px-35 py-20 bg-base-100">
                    <div className="mx-auto max-w-6xl">
                        <div className="text-center">
                            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-base-content">
                                Millions of Data Points. One Hidden Story.
                            </h1>

                            <p className="mt-6 text-lg text-base-content/60 max-w-2xl mx-auto">
                                Formula 1 cars generate vast amounts of telemetry, timing, and
                                strategy data every race, but for most fans and analysts, that
                                insight remains inaccessible, fragmented, or overwhelming.
                            </p>
                        </div>

                        <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                            <ProblemCard
                                icon="📡"
                                title="Raw Telemetry"
                                description="Speed, throttle, tyre data and weather metrics exist, but
                                        rarely in digestible form."
                            />

                            <ProblemCard
                                icon="🧩"
                                title="Fragmented APIs"
                                description="Historical results, live timing, and telemetry live across separate systems."
                            />

                            <ProblemCard
                                icon="⏱️"
                                title="No Race Reconstruction"
                                description="Most platforms show final standings, not how strategy and battles unfolded."
                            />

                            <ProblemCard
                                icon="🎛️"
                                title="High Technical Barrier"
                                description="Meaningful analysis often requires scripts, notebooks, or advanced tooling."
                            />
                        </div>

                        <div className="mt-12 text-center">
                            <p className="text-lg text-base-content/70 max-w-3xl mx-auto">
                                The result? Fans can't see the full story, journalists can't easily
                                visualise insights, and analysts must build everything from scratch.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Tech Stack */}
                <section className="-mx-6 md:-mx-35 px-6 md:px-35 py-20 bg-base-200">
                    <div className="mx-auto max-w-6xl">
                        <div className="text-center">
                            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-base-content">
                                Built Like a Race System.
                            </h1>

                            <p className="mt-6 text-lg text-base-content/60 max-w-2xl mx-auto">
                                A modern full-stack setup designed for fast visualisation, reliable
                                data fetching, and scalable analysis.
                            </p>
                        </div>

                        <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3 items-center">
                            <div className="card bg-base-100 shadow-sm">
                                <div className="card-body items-center text-center">
                                    <div className="text-3xl">⚛️</div>
                                    <h3 className="card-title">React + TypeScript</h3>
                                    <p className="text-base-content/60">
                                        A responsive UI built for interactive dashboards and
                                        playback.
                                    </p>
                                </div>
                            </div>

                            <div className="card bg-base-100 shadow-sm">
                                <div className="card-body items-center text-center">
                                    <div className="text-3xl">🐍</div>
                                    <h3 className="card-title">Django REST API</h3>
                                    <p className="text-base-content/60">
                                        Backend endpoints that structure session data for the
                                        frontend.
                                    </p>
                                </div>
                            </div>

                            <div className="card bg-base-100 shadow-sm">
                                <div className="card-body items-center text-center">
                                    <div className="text-3xl">📡</div>
                                    <h3 className="card-title">OpenF1 + Ergast / FastF1</h3>
                                    <p className="text-base-content/60">
                                        Trusted race data sources for telemetry, timing, and
                                        history.
                                    </p>
                                </div>
                            </div>

                            <div className="card bg-base-100 shadow-sm">
                                <div className="card-body items-center text-center">
                                    <div className="text-3xl">🧠</div>
                                    <h3 className="card-title">Caching Layer</h3>
                                    <p className="text-base-content/60">
                                        Built in the FastF1 library to speed up repeated data access
                                        and report generation.
                                    </p>
                                </div>
                            </div>

                            <div className="card bg-base-100 shadow-sm">
                                <div className="card-body items-center text-center">
                                    <div className="text-3xl">📈</div>
                                    <h3 className="card-title">Data Visualisation</h3>
                                    <p className="text-base-content/60">
                                        Plotly charts and comparisons built for analysis, reporting,
                                        and export.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Call To Action */}
                <section className="relative -mx-6 md:-mx-35 px-6 md:px-35 py-24 overflow-hidden">
                    {/* Background Image */}
                    <div
                        className="absolute inset-0 bg-cover bg-center"
                        style={{ backgroundImage: `url("${call_bg}")` }}
                    />

                    {/* Dark Overlay */}
                    <div className="absolute inset-0 bg-black/90" />

                    {/* Content */}
                    <div className="relative mx-auto max-w-6xl text-center text-white">
                        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
                            Ready to Dive In?
                        </h1>

                        <p className="mt-6 text-lg text-white/80 max-w-2xl mx-auto">
                            Pick a starting point. Explore races, compare drivers, or jump straight
                            into the dashboards.
                        </p>

                        <div className="mt-10 flex flex-col sm:flex-row flex-wrap justify-center items-center gap-4">
                            <a href="/race-viewer" className="btn btn-primary btn-wide">
                                Start Exploring Races
                            </a>

                            <a href="/teams" className="btn btn-primary btn-wide">
                                Compare Teams
                            </a>

                            <a href="/drivers" className="btn btn-primary btn-wide">
                                Find a Driver
                            </a>
                        </div>

                        <div className="mt-8">
                            <p className="text-sm text-white/60">
                                No signup. No paywalls. Just racing data.
                            </p>
                        </div>
                    </div>
                </section>
            </div>
            <Footer />
        </div>
    );
}

function Step({
    number,
    title,
    description,
}: {
    number: string;
    title: string;
    description: string;
}) {
    return (
        <div className="flex flex-col items-center text-center">
            <div
                className="
        h-14 w-14
    flex items-center justify-center
    rounded-full
    bg-(--color-primary)
    text-black
    font-semibold
    text-lg
    shadow-lg
      "
            >
                {number}
            </div>

            <h3 className="mt-6 text-lg font-semibold text-base-content">{title}</h3>

            <p className="mt-3 text-base-content/60 max-w-xs">{description}</p>
        </div>
    );
}
