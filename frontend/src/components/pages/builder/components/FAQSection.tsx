import { useState } from 'react';
import useDarkModeStore from '../../../../../store/darkmode.store';
import { motion, AnimatePresence } from 'framer-motion';
import { faqData } from '../constants/faqData';

function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const { isDarkMode } = useDarkModeStore();

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="py-12 md:py-20">
      <div className="text-center px-4">
        <h2 className={`text-3xl sm:text-4xl md:text-5xl font-bold mb-3 md:mb-4 bg-gradient-to-r bg-clip-text text-transparent ${
          isDarkMode
            ? 'from-white to-gray-400'
            : 'from-purple-600 to-pink-600'
        }`}>
          Frequently Asked Questions
        </h2>
        <div className="w-24 md:w-32 h-1 mb-4 bg-gradient-to-r from-purple-500 to-pink-500 mx-auto rounded-full" />
      </div>

      <div className="max-w-4xl mx-auto space-y-3 md:space-y-4 px-4">
        {faqData.map((faq, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`backdrop-blur-sm rounded-xl overflow-hidden transition-all duration-300 ${
              isDarkMode
                ? 'bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 hover:border-gray-600/50'
                : 'bg-white/70 border border-purple-200/50 hover:border-purple-300/50 shadow-sm hover:shadow-md'
            }`}
          >
            <button
              onClick={() => toggleFAQ(index)}
              className="w-full flex items-center justify-between p-4 md:p-6 text-left"
            >
              <span className={`text-base md:text-lg font-semibold pr-4 md:pr-8 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {faq.question}
              </span>
              <motion.svg
                className={`w-5 h-5 md:w-6 md:h-6 flex-shrink-0 ${isDarkMode ? 'text-gray-400' : 'text-purple-500'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                animate={{ rotate: openIndex === index ? 180 : 0 }}
                transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </motion.svg>
            </button>
            <AnimatePresence initial={false}>
              {openIndex === index && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ 
                    height: "auto", 
                    opacity: 1,
                    transition: {
                      height: {
                        duration: 0.6,
                        ease: [0.4, 0, 0.2, 1]
                      },
                      opacity: {
                        duration: 0.5,
                        delay: 0.1,
                        ease: "easeOut"
                      }
                    }
                  }}
                  exit={{ 
                    height: 0, 
                    opacity: 0,
                    transition: {
                      height: {
                        duration: 0.5,
                        ease: [0.4, 0, 0.2, 1]
                      },
                      opacity: {
                        duration: 0.3,
                        ease: "easeIn"
                      }
                    }
                  }}
                  className="overflow-hidden"
                >
                  <motion.div 
                    className={`px-4 md:px-6 pb-4 md:pb-6 text-sm md:text-base leading-relaxed ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-600'
                    }`}
                    initial={{ y: -10 }}
                    animate={{ y: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                  >
                    {faq.answer}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Social Media Icons */}
      <div className="flex justify-center gap-3 md:gap-4 mt-12 md:mt-16 px-4">
        <a
          href="#"
          className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center transition-all ${
            isDarkMode
              ? 'bg-gray-800/50 hover:bg-blue-600/30 border border-gray-700/50'
              : 'bg-white/70 hover:bg-blue-100 border border-purple-200/50'
          }`}
        >
          <svg className="w-5 h-5 md:w-6 md:h-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
          </svg>
        </a>
        <a
          href="#"
          className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center transition-all ${
            isDarkMode
              ? 'bg-gray-800/50 hover:bg-blue-500/30 border border-gray-700/50'
              : 'bg-white/70 hover:bg-blue-100 border border-purple-200/50'
          }`}
        >
          <svg className="w-5 h-5 md:w-6 md:h-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm4.441 9.442c.002.126.003.253.003.38 0 3.874-2.948 8.338-8.338 8.338a8.29 8.29 0 01-4.489-1.314c.229.027.462.04.698.04a5.87 5.87 0 003.634-1.253 2.931 2.931 0 01-2.735-2.033 2.93 2.93 0 001.322-.05 2.928 2.928 0 01-2.347-2.868v-.037c.394.219.845.35 1.325.365a2.928 2.928 0 01-.906-3.908 8.309 8.309 0 006.032 3.058 2.928 2.928 0 014.988-2.67 5.873 5.873 0 001.858-.71 2.937 2.937 0 01-1.287 1.619 5.858 5.858 0 001.682-.461 5.952 5.952 0 01-1.462 1.516z" />
          </svg>
        </a>
        <a
          href="#"
          className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center transition-all ${
            isDarkMode
              ? 'bg-gray-800/50 hover:bg-gray-600/30 border border-gray-700/50'
              : 'bg-white/70 hover:bg-gray-200 border border-purple-200/50'
          }`}
        >
          <svg className={`w-5 h-5 md:w-6 md:h-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} fill="currentColor" viewBox="0 0 24 24">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
          </svg>
        </a>
        <a
          href="#"
          className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center transition-all ${
            isDarkMode
              ? 'bg-gray-800/50 hover:bg-gray-600/30 border border-gray-700/50'
              : 'bg-white/70 hover:bg-gray-200 border border-purple-200/50'
          }`}
        >
          <svg className={`w-5 h-5 md:w-6 md:h-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </a>
      </div>

      {/* Footer Links */}
      <div className={`flex flex-wrap justify-center gap-4 md:gap-8 mt-6 md:mt-8 text-xs md:text-sm px-4 ${
        isDarkMode ? 'text-gray-500' : 'text-gray-600'
      }`}>
        <a href="#" className={`transition-colors ${
          isDarkMode ? 'hover:text-gray-300' : 'hover:text-purple-600'
        }`}>
          Privacy Policy
        </a>
        <span className="hidden sm:inline">•</span>
        <a href="#" className={`transition-colors ${
          isDarkMode ? 'hover:text-gray-300' : 'hover:text-purple-600'
        }`}>
          Terms of Service
        </a>
      </div>
    </section>
  );
}

export default FAQSection;



