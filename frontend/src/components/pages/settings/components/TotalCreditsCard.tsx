import { Wallet } from 'lucide-react'
import useDarkModeStore from '../../../../../store/darkmode.store'

interface TotalCreditsCardProps {
  totalCredits: number
  creditsUsed: number
  isLoading: boolean
}

export const TotalCreditsCard = ({ totalCredits, creditsUsed, isLoading }: TotalCreditsCardProps) => {
  const { isDarkMode } = useDarkModeStore()
  const totalCreditsSum = totalCredits + creditsUsed

  return (
    <div className={`p-4 rounded-xl border ${
      isDarkMode 
        ? 'bg-gray-800/50 border-gray-700' 
        : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          isDarkMode 
            ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20' 
            : 'bg-gradient-to-br from-purple-100 to-pink-100'
        }`}>
          <Wallet className={`w-5 h-5 ${
            isDarkMode 
              ? 'text-purple-400' 
              : 'text-purple-600'
          }`} />
        </div>
        <div className="flex-1">
          <p className={`text-sm ${
            isDarkMode ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Total Credits
          </p>
          <p className={`text-3xl font-bold ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {isLoading ? '...' : totalCreditsSum}
          </p>
        </div>
      </div>
    </div>
  )
}

