import { useEffect, useMemo, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import type { ISourceOptions } from "@tsparticles/engine";
import useDarkModeStore from "../../../store/darkmode.store";

function ParticlesBackground() {
    const { isDarkMode } = useDarkModeStore();
    const [init, setInit] = useState(false);

    useEffect(() => {
        initParticlesEngine(async (engine) => {
            await loadSlim(engine);
        }).then(() => {
            setInit(true);
        });
    }, []);

    const options: ISourceOptions = useMemo(
        () => ({
            background: {
                color: {
                    value: "transparent",
                },
            },
            fpsLimit: 120,
            interactivity: {
                events: {
                    onHover: {
                        enable: true,
                        mode: "grab",
                    },
                    resize: {
                        enable: true,
                    } as any,
                },
                modes: {
                    grab: {
                        distance: 140,
                        links: {
                            opacity: 0.3,
                        },
                    },
                },
            },
            particles: {
                color: {
                    value: isDarkMode 
                        ? ["#a855f7", "#ec4899", "#f59e0b", "#8b5cf6"] 
                        : ["#c084fc", "#f0abfc", "#fbbf24", "#a78bfa"],
                },
                links: {
                    color: isDarkMode ? "#a855f7" : "#c084fc",
                    distance: 150,
                    enable: false,
                    opacity: 0.2,
                    width: 1,
                },
                move: {
                    direction: "none",
                    enable: true,
                    outModes: {
                        default: "bounce",
                    },
                    random: true,
                    speed: 0.8,
                    straight: false,
                },
                number: {
                    density: {
                        enable: true,
                    },
                    value: isDarkMode ? 80 : 50,
                },
                opacity: {
                    value: isDarkMode ? { min: 0.3, max: 0.7 } : { min: 0.15, max: 0.4 },
                    animation: {
                        enable: true,
                        speed: 0.5,
                        sync: false,
                    },
                },
                shape: {
                    type: "circle",
                },
                size: {
                    value: isDarkMode ? { min: 2, max: 8 } : { min: 3, max: 10 },
                    animation: {
                        enable: true,
                        speed: 2,
                        sync: false,
                    },
                },
            },
            detectRetina: true,
        }),
        [isDarkMode]
    );

    if (!init) {
        return null;
    }

    return (
        <Particles
            id="tsparticles"
            options={options}
            className="fixed inset-0 -z-10"
        />
    );
}

export default ParticlesBackground;

