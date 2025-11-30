import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Send, CheckCircle, Clock } from 'lucide-react'
import useDarkModeStore from '../../../../../store/darkmode.store'
import { useResendVerification } from '../hooks/useResendVerification'

function CheckEmail() {
  const { isDarkMode } = useDarkModeStore()
  const { resendEmail, isLoading } = useResendVerification()
  const [email, setEmail] = useState('')
  const [countdown, setCountdown] = useState(0)

  // Load email from localStorage (set during registration)
  useEffect(() => {
    const savedEmail = localStorage.getItem('verificationEmail')
    if (savedEmail) {
      setEmail(savedEmail)
    }
  }, [])

  // Countdown timer for resend button
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  const handleResendEmail = async () => {
    if (!email) {
      return
    }
    await resendEmail(email)
    setCountdown(40) // Start 40 second countdown
  }

  const isButtonDisabled = countdown > 0 || isLoading || !email

  return (
    <div className={`min-h-screen flex items-center justify-center px-4 transition-colors duration-300 ${
      isDarkMode
        ? 'bg-gradient-to-br from-gray-900 via-[#0a0a0a] to-gray-900'
        : 'bg-gradient-to-br from-purple-50 via-white to-pink-50'
    }`}>
      <div className="w-full max-w-md">

        {/* Card */}
        <div className={`rounded-2xl shadow-2xl border backdrop-blur-sm transition-all duration-300 ${
          isDarkMode
            ? 'bg-gray-900/90 border-gray-800 shadow-purple-900/20'
            : 'bg-white/80 border-purple-200 shadow-purple-200/50'
        }`}>
          <div className="p-8">
            {/* Success Icon */}
            <div className="flex justify-center mb-6">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center ${
                isDarkMode
                  ? 'bg-gradient-to-br from-green-500/20 to-emerald-500/20'
                  : 'bg-gradient-to-br from-green-100 to-emerald-100'
              }`}>
                <CheckCircle className={`w-10 h-10 ${
                  isDarkMode ? 'text-green-400' : 'text-green-600'
                }`} />
              </div>
            </div>

            {/* Title */}
            <h1 className={`text-3xl font-bold text-center mb-3 ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Check Your Email!
            </h1>

            {/* Success Message */}
            <div className={`mb-6 p-4 rounded-lg ${
              isDarkMode
                ? 'bg-green-500/10 border border-green-500/20'
                : 'bg-green-50 border border-green-200'
            }`}>
              <p className={`text-center text-sm ${
                isDarkMode ? 'text-green-400' : 'text-green-700'
              }`}>
                <strong>Registration successful!</strong>
                <br />
                We've sent a verification link to your email address.
              </p>
            </div>

            {/* Email Display */}
            <p className={`text-center mb-8 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Verification email sent to:
              <br />
              <span className={`font-semibold text-lg ${
                isDarkMode ? 'text-purple-400' : 'text-purple-600'
              }`}>
                {email || 'your email'}
              </span>
            </p>

            {/* Instructions */}
            <div className={`mb-6 p-4 rounded-lg ${
              isDarkMode
                ? 'bg-purple-500/10 border border-purple-500/20'
                : 'bg-purple-50 border border-purple-200'
            }`}>
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                <strong>Next steps:</strong>
                <br />
                1. Check your email inbox
                <br />
                2. Click the verification link in the email
                <br />
                3. Your account will be activated
                <br />
                4. You can then sign in to access your dashboard
              </p>
            </div>

            {/* Resend Button */}
            <button
              onClick={handleResendEmail}
              disabled={isButtonDisabled}
              className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all duration-300 ${
                isButtonDisabled
                  ? isDarkMode
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : isDarkMode
                    ? 'bg-gradient-to-r from-purple-500 via-purple-400 to-pink-400 text-white hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105'
                    : 'bg-gradient-to-r from-purple-500 via-purple-400 to-pink-400 text-white hover:shadow-lg hover:shadow-purple-500/30 hover:scale-105'
              }`}
            >
              {countdown > 0 ? (
                <>
                  <Clock className="w-5 h-5" />
                  Resend in {countdown}s
                </>
              ) : isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Resend Verification Email
                </>
              )}
            </button>

            {/* Help Text */}
            <div className={`mt-6 p-4 rounded-lg ${
              isDarkMode
                ? 'bg-yellow-500/10 border border-yellow-500/20'
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <p className={`text-sm ${
                isDarkMode ? 'text-yellow-300' : 'text-yellow-700'
              }`}>
                <strong>Can't find the email?</strong>
                <br />
                • Check your spam or junk folder
                <br />
                • Make sure {email} is correct
                <br />
                • Wait a few minutes and check again
                <br />
                • Click the resend button above
              </p>
            </div>

            {/* Footer Link */}
            <div className="mt-6 text-center">
              <Link
                to="/auth/signin"
                className={`text-sm font-medium transition-colors ${
                  isDarkMode
                    ? 'text-purple-400 hover:text-purple-300'
                    : 'text-purple-600 hover:text-purple-700'
                }`}
              >
                Already verified? Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CheckEmail