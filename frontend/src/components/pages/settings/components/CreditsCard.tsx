import { Wallet, Info } from 'lucide-react'
import { useState } from 'react'
import useDarkModeStore from '../../../../../store/darkmode.store'
import { CreditsInfoPopup } from './CreditsInfoPopup'
import { TotalCreditsCard } from './TotalCreditsCard'
import { CreditsUsageProgress } from './CreditsUsageProgress'

interface CreditsCardProps {
  totalCredits: number
  creditsUsed: number
  isLoading: boolean
}

export const CreditsCard = ({ totalCredits, creditsUsed, isLoading }: CreditsCardProps) => {
  const { isDarkMode } = useDarkModeStore()
  const [showCreditsInfo, setShowCreditsInfo] = useState(false)

  return (
    <div className={`rounded-2xl border p-6 relative ${
      isDarkMode 
        ? 'bg-gray-900/50 border-gray-800' 
        : 'bg-white border-gray-200 shadow-lg'
    }`}>
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          isDarkMode ? 'bg-green-500/20' : 'bg-green-100'
        }`}>
          <Wallet className={`w-5 h-5 ${
            isDarkMode ? 'text-green-400' : 'text-green-600'
          }`} />
        </div>
        <h2 className={`text-2xl font-bold ${
          isDarkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Credits
        </h2>
        <button
          onClick={() => setShowCreditsInfo(!showCreditsInfo)}
          className={`ml-auto p-2 rounded-lg transition-colors ${
            isDarkMode 
              ? 'hover:bg-gray-800 text-gray-400 hover:text-white' 
              : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
          }`}
        >
          <Info className="w-5 h-5" />
        </button>
      </div>

      {/* Credits Info Popup */}
      {showCreditsInfo && (
        <CreditsInfoPopup onClose={() => setShowCreditsInfo(false)} />
      )}

      <div className="space-y-4">
        <TotalCreditsCard 
          totalCredits={totalCredits} 
          creditsUsed={creditsUsed}
          isLoading={isLoading} 
        />
        <CreditsUsageProgress 
          creditsUsed={creditsUsed} 
          totalCredits={totalCredits} 
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}

