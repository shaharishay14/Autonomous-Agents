import { Link, QrCode, Code } from 'lucide-react';
import type { TabsProps } from './types';

export function ShareModalTabs({ activeTab, setActiveTab, isDarkMode }: TabsProps) {
  const tabBaseClass = "flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all";
  
  const getTabClass = (tab: string) => {
    const isActive = activeTab === tab;
    
    if (isActive) {
      return `${tabBaseClass} ${
        isDarkMode
          ? 'bg-white/10 text-white'
          : 'bg-gray-900 text-white'
      }`;
    }
    
    return `${tabBaseClass} ${
      isDarkMode
        ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }`;
  };

  return (
    <div className="flex gap-2 mb-6">
      <button
        onClick={() => setActiveTab('link')}
        className={getTabClass('link')}
      >
        <Link className="w-4 h-4" />
        Link
      </button>
      <button
        onClick={() => setActiveTab('qr')}
        className={getTabClass('qr')}
      >
        <QrCode className="w-4 h-4" />
        QR
      </button>
      <button
        onClick={() => setActiveTab('embed')}
        className={getTabClass('embed')}
      >
        <Code className="w-4 h-4" />
        Embed
      </button>
    </div>
  );
}

