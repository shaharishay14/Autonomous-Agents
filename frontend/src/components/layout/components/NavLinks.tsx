import { NavLink } from "react-router-dom";
import { navLinks } from "../constants/navLinks";

interface NavLinksProps {
    isDarkMode: boolean;
    onLinkClick?: () => void;
    isMobile?: boolean;
}

export const NavLinks = ({ isDarkMode, onLinkClick, isMobile = false }: NavLinksProps) => {
    return (
        <div className={isMobile ? "flex flex-col gap-2" : "hidden md:flex items-center gap-2"}>
            {navLinks.map((link) => {
                const Icon = link.icon;
                return (
                    <NavLink
                        key={link.to}
                        to={link.to}
                        onClick={onLinkClick}
                        className={({ isActive }) =>
                            `${isMobile ? 'px-4 py-3' : 'px-4 py-2'} rounded-lg font-semibold transition-all duration-300 flex items-center ${isMobile ? 'gap-3' : 'gap-2'} border ${isActive
                                ? isDarkMode
                                    ? `text-purple-500 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/30 ${!isMobile ? 'shadow-[0_0_20px_rgba(168,85,247,0.4),0_0_40px_rgba(168,85,247,0.2),0_0_60px_rgba(236,72,153,0.1)]' : ''}`
                                    : 'text-purple-700 bg-gradient-to-r from-purple-200 to-pink-200 border-purple-300 shadow-md'
                                : isDarkMode
                                    ? 'text-gray-400 hover:text-white hover:bg-purple-500/10 border-transparent hover:border-purple-500/30'
                                    : 'text-gray-700 hover:text-purple-700 hover:bg-purple-100/70 border-transparent hover:border-purple-300'
                            }`
                        }
                    >
                        <Icon className={isMobile ? "w-5 h-5" : "w-4 h-4"} />
                        {link.label}
                    </NavLink>
                );
            })}
        </div>
    );
};

