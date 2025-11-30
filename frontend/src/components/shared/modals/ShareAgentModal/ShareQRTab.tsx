import { useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { QrCode, Download } from 'lucide-react';
import type { ShareQRTabProps } from './types';

export function ShareQRTab({ isDarkMode, agentLink }: ShareQRTabProps) {
  const qrRef = useRef<HTMLDivElement>(null);

  const handleDownload = () => {
    if (!qrRef.current) return;
    
    const svg = qrRef.current.querySelector('svg');
    if (!svg) return;

    // Create canvas to convert SVG to PNG
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const svgData = new XMLSerializer().serializeToString(svg);
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx?.drawImage(img, 0, 0);
      
      // Download as PNG
      const pngFile = canvas.toDataURL('image/png');
      const downloadLink = document.createElement('a');
      downloadLink.download = 'agent-qr-code.png';
      downloadLink.href = pngFile;
      downloadLink.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  return (
    <div className="text-center">
      <div className="flex items-center gap-2 mb-4 justify-center">
        <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
          <QrCode className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            📱 QR Magic Code
          </h3>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Scan to instantly access your agent
          </p>
        </div>
      </div>

      {/* Real QR Code */}
      <div 
        ref={qrRef}
        className="inline-block p-4 rounded-2xl mb-4 bg-white shadow-lg"
      >
        <QRCodeSVG
          value={agentLink}
          size={180}
          level="H"
          includeMargin={true}
          fgColor="#000000"
          bgColor="#ffffff"
        />
      </div>

      <button
        onClick={handleDownload}
        className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 rounded-xl text-white font-medium transition-all flex items-center justify-center gap-2 shadow-lg"
      >
        <Download className="w-5 h-5" />
        📥 Download & Print QR
      </button>
    </div>
  );
}

