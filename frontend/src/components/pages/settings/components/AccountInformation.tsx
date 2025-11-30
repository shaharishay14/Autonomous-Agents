import { Mail, Crown, Users, User } from 'lucide-react'
import useDarkModeStore from '../../../../../store/darkmode.store'
import { useUserStore } from '../../../../../store/user.store'

export const AccountInformation = () => {
  const { isDarkMode } = useDarkModeStore()
  const { user } = useUserStore()

  return (
    <div className={`rounded-2xl border p-6 ${
      isDarkMode 
        ? 'bg-gray-900/50 border-gray-800' 
        : 'bg-white border-gray-200 shadow-lg'
    }`}>
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          isDarkMode ? 'bg-blue-500/20' : 'bg-blue-100'
        }`}>
          <Users className={`w-5 h-5 ${
            isDarkMode ? 'text-blue-400' : 'text-blue-600'
          }`} />
        </div>
        <h2 className={`text-2xl font-bold ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Account Information
        </h2>
      </div>

      <div className="space-y-4">
        {/* Username */}
        <div className={`p-4 rounded-xl border ${
          isDarkMode 
            ? 'bg-gray-800/50 border-gray-700' 
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-purple-500/20' : 'bg-purple-100'
            }`}>
              <User className={`w-5 h-5 ${
                isDarkMode ? 'text-purple-400' : 'text-purple-600'
              }`} />
            </div>
            <div className="flex-1">
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                Username
              </p>
              <p className={`text-base font-medium ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {user?.username || 'Not available'}
              </p>
            </div>
          </div>
        </div>

        {/* Email */}
        <div className={`p-4 rounded-xl border ${
          isDarkMode 
            ? 'bg-gray-800/50 border-gray-700' 
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-gray-700' : 'bg-gray-200'
            }`}>
              <Mail className={`w-5 h-5 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-600'
              }`} />
            </div>
            <div className="flex-1">
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                Email Address
              </p>
              <p className={`text-base font-medium ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {user?.email || 'Not available'}
              </p>
            </div>
          </div>
        </div>

        {/* Current Plan */}
        <div className={`p-4 rounded-xl border ${
          isDarkMode 
            ? 'bg-gray-800/50 border-gray-700' 
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-yellow-500/20' : 'bg-yellow-100'
            }`}>
              <Crown className={`w-5 h-5 ${
                isDarkMode ? 'text-yellow-400' : 'text-yellow-600'
              }`} />
            </div>
            <div className="flex-1">
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                Current Plan
              </p>
              <p className={`text-base font-medium ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Free
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

