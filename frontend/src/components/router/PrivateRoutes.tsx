import { Navigate, Outlet } from "react-router-dom"
import { useUserStore } from "../../../store/user.store"
import { useEffect } from "react"



function PrivateRoutes() {
    const { isAuthenticated, user, clearUser, setIsAuthenticated } = useUserStore((state) => state)

    // Check if user is authenticated
    if (!isAuthenticated) {
        return <Navigate to="/auth/signin" />
    }

    // Check if user's email is verified
    useEffect(() => {
        if (user && user.is_verified === false) {
            // Clear authentication and redirect to verification prompt
            clearUser()
            setIsAuthenticated(false)
            // Save email for verification prompt page
            localStorage.setItem('verificationEmail', user.email)
        }
    }, [user, clearUser, setIsAuthenticated])

    // If user is not verified, redirect to verification prompt
    if (user && user.is_verified === false) {
        return <Navigate to="/auth/verify-email-prompt" />
    }

    return (
        <Outlet />
    )
}

export default PrivateRoutes