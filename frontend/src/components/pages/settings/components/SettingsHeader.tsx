import { Settings as SettingsIcon } from 'lucide-react'
import useDarkModeStore from '../../../../../store/darkmode.store'

export const SettingsHeader = () => {
  const { isDarkMode } = useDarkModeStore()

  return (
    <div className="flex items-center gap-4 mb-12">
      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
        isDarkMode 
          ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
          : 'bg-gradient-to-br from-purple-400 to-pink-400'
      }`}>
        <SettingsIcon className="w-8 h-8 text-white" />
      </div>
      <div>
        <h1 className={`text-4xl font-bold ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Settings
        </h1>
        <p className={`text-lg ${
          isDarkMode ? 'text-gray-400' : 'text-gray-600'
        }`}>
          Manage your account and preferences
        </p>
      </div>
    </div>
  )
}

