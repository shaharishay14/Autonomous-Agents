import useDarkModeStore from '../../../../store/darkmode.store'
import { useGetCredits } from './hooks'
import { SettingsHeader, AccountInformation, CreditsCard } from './components'

function Settings() {
  const { isDarkMode } = useDarkModeStore()
  const { credits, isLoading: isLoadingCredits } = useGetCredits()

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode ? 'bg-[#0a0a0a]' : 'bg-gradient-to-br from-purple-50 via-white to-pink-50'
    }`}>
      <div className="max-w-7xl mx-auto px-8 py-12">
        <SettingsHeader />

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AccountInformation />
          
          <CreditsCard 
            totalCredits={credits?.total_credits ?? 0}
            creditsUsed={credits?.credits_used ?? 0}
            isLoading={isLoadingCredits}
          />
        </div>
      </div>
    </div>
  )
}

export default Settings

