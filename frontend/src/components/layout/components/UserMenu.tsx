import { Link } from "react-router-dom";
import { Settings, LogOut, ChevronDown } from "lucide-react";
import { type RefObject } from "react";

interface UserMenuProps {
    isDarkMode: boolean;
    user: { email: string };
    isUserMenuOpen: boolean;
    toggleUserMenu: () => void;
    setIsUserMenuOpen: (value: boolean) => void;
    logout: () => void;
    userMenuRef: RefObject<HTMLDivElement | null>;
    getInitial: () => string;
}

export const UserMenu = ({
    isDarkMode,
    user,
    isUserMenuOpen,
    toggleUserMenu,
    setIsUserMenuOpen,
    logout,
    userMenuRef,
    getInitial
}: UserMenuProps) => {
    return (
        <div className="relative" ref={userMenuRef}>
            <button
                onClick={toggleUserMenu}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all duration-200 border ${isDarkMode
                        ? 'bg-gray-800/50 hover:bg-gray-700/50 text-white border-gray-700 hover:border-gray-600'
                        : 'bg-white hover:bg-gray-50 text-gray-900 border-gray-300 hover:border-gray-400 shadow-sm'
                    }`}
            >
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span className="font-medium">{user.email}</span>
                <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isUserMenuOpen && (
                <div className={`absolute right-0 mt-2 w-72 rounded-xl shadow-2xl border overflow-hidden ${isDarkMode
                        ? 'bg-gray-900 border-gray-700'
                        : 'bg-white border-gray-200'
                    }`}>
                    <div className={`px-4 py-3 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'
                        }`}>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                                {getInitial()}
                            </div>
                            <div className="flex-1">
                                <p className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    {user.email}
                                </p>
                                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                    Free Plan
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="py-2">
                        <Link
                            to="/settings"
                            onClick={() => setIsUserMenuOpen(false)}
                            className={`px-4 py-2 flex items-center gap-3 transition-colors ${isDarkMode
                                    ? 'text-gray-300 hover:bg-gray-800 hover:text-white'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                                }`}
                        >
                            <Settings className="w-4 h-4" />
                            <span className="font-medium">Settings</span>
                        </Link>

                        <button
                            onClick={() => {
                                setIsUserMenuOpen(false);
                                logout();
                            }}
                            className={`w-full px-4 py-2 flex items-center gap-3 transition-colors ${isDarkMode
                                    ? 'text-gray-300 hover:bg-gray-800 hover:text-white'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                                }`}
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="font-medium">Sign Out</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

