import { Link } from "react-router-dom";
import hero_bg from "../assets/hero-bg.jpg";
import logo from "../assets/logo.png";

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
                className="hero h-[500px] relative"
                style={{
                    backgroundImage: `url("${hero_bg}")`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                }}
            >
                {/* Dark overlay */}
                <div className="absolute inset-0 bg-linear-to-r from-black/80 via-black/50 to-black/80"></div>

                <div className="hero-content text-center text-neutral-content relative z-10">
                    <div className="max-w-2xl">
                        <div className="flex justify-center items-center">
                            <img
                                src={logo}
                                alt="F1 Race Viewer"
                                className="h-12 w-auto px-4 object-contain mb-8"
                            />
                        </div>
                        <h1 className="text-5xl font-bold">Explore Formula 1 Data</h1>
                        <p className="pb-6 pt-4 text-lg">
                            Visualise race sessions, compare drivers, analyse teams, and dive into
                            historical F1 statistics all in one place.
                        </p>
                        <Link to="/race-viewer" className="btn btn-primary">
                            Start Exploring
                        </Link>
                    </div>
                </div>
            </div>

            {/* Expandable Content Section */}
            <section className="py-16 px-6 max-w-6xl mx-auto">
                <h2 className="text-3xl font-bold mb-6">What You Can Explore</h2>
                <p className="text-lg opacity-80">
                    Add feature cards, statistics previews, or screenshots of your dashboard here.
                </p>
            </section>
        </div>
    );
}
