import useDarkModeStore from "../../../store/darkmode.store";
import { useUserStore } from "../../../store/user.store";
import { useLogout } from "../pages/auth/hooks";
import { useNavMenu } from "./hooks/useNavMenu";
import {
    NavLogo,
    DarkModeToggle,
    NavLinks,
    UserMenu,
    AuthButtons,
    MobileMenuButton,
    MobileMenuOverlay,
    MobileMenu
} from "./components";

function Nav() {
    const { isDarkMode, toggleDarkMode } = useDarkModeStore();
    const { user, isAuthenticated } = useUserStore();
    const { logout } = useLogout();
    const {
        isMobileMenuOpen,
        isUserMenuOpen,
        userMenuRef,
        toggleMobileMenu,
        closeMobileMenu,
        toggleUserMenu,
        setIsUserMenuOpen
    } = useNavMenu();

    // קבלת האות הראשונה של המייל
    const getInitial = () => {
        return user?.email?.charAt(0).toUpperCase() || 'U';
    };

    return (
        <>
            <nav className={`relative z-50 transition-colors duration-300 border-b backdrop-blur-md ${isDarkMode
                    ? 'bg-[#0a0a0a]/80 border-gray-800'
                    : 'bg-white/70 border-purple-200 shadow-lg'
                }`}>
                <div className="max-w-7xl mx-auto px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Left Section */}
                        <div className="flex items-center gap-12">
                            <NavLogo isDarkMode={isDarkMode} />
                            <NavLinks isDarkMode={isDarkMode} />
                        </div>

                        {/* Right Section - Auth Buttons / User Menu */}
                        <div className="hidden md:flex items-center gap-3">
                            <DarkModeToggle
                                isDarkMode={isDarkMode}
                                toggleDarkMode={toggleDarkMode}
                                className="p-2.5"
                            />

                            {isAuthenticated && user ? (
                                <UserMenu
                                    isDarkMode={isDarkMode}
                                    user={user}
                                    isUserMenuOpen={isUserMenuOpen}
                                    toggleUserMenu={toggleUserMenu}
                                    setIsUserMenuOpen={setIsUserMenuOpen}
                                    logout={logout}
                                    userMenuRef={userMenuRef}
                                    getInitial={getInitial}
                                />
                            ) : (
                                <AuthButtons isDarkMode={isDarkMode} />
                            )}
                        </div>

                        {/* Mobile Menu Button */}
                        <MobileMenuButton
                            isDarkMode={isDarkMode}
                            isMobileMenuOpen={isMobileMenuOpen}
                            toggleMobileMenu={toggleMobileMenu}
                        />
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <MobileMenuOverlay
                    isDarkMode={isDarkMode}
                    closeMobileMenu={closeMobileMenu}
                />
            )}

            {/* Mobile Menu Drawer */}
            <MobileMenu
                isDarkMode={isDarkMode}
                isMobileMenuOpen={isMobileMenuOpen}
                closeMobileMenu={closeMobileMenu}
                toggleDarkMode={toggleDarkMode}
                isAuthenticated={isAuthenticated}
                user={user}
                getInitial={getInitial}
                logout={logout}
            />
        </>
    )
}

export default Nav
