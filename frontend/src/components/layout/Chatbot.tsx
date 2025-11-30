import { useState, useRef, useEffect } from 'react';
import { X, Send, MessageCircle, Paperclip } from 'lucide-react';
import useDarkModeStore from '../../../store/darkmode.store';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const quickQuestions = [
  "How do I start with Kgen21?",
  "Show me Kgen21's key features.",
  "Help me troubleshoot login issues.",
];

function Chatbot() {
  const { isDarkMode } = useDarkModeStore();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isFirstOpen, setIsFirstOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (text: string = inputValue) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Thanks for your message! Our support team will get back to you shortly.",
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    }, 1000);
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleOpen = () => {
    setIsOpen(true);
    if (isFirstOpen) {
      setIsFirstOpen(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50">
          <button
            onClick={handleOpen}
            className="relative w-16 h-16 flex items-center justify-center group"
            aria-label="Open chat"
          >
            {/* Outer Gradient Ring */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 p-[3px] group-hover:p-[3.5px] transition-all">
              <div className={`w-full h-full rounded-full ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`} />
            </div>
            
            {/* Glow Effect */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 blur-xl opacity-20 group-hover:opacity-40 transition-opacity" />
            
            {/* Icon */}
            <MessageCircle 
              size={22} 
              strokeWidth={2.5}
              className={`relative z-10 ${isDarkMode ? 'text-white' : 'text-gray-900'} group-hover:scale-110 transition-transform`}
            />
          </button>
        </div>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={`fixed bottom-6 right-6 w-[400px] h-[600px] rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden ${
            isDarkMode
              ? 'bg-gray-900 border border-gray-700'
              : 'bg-white border border-gray-200'
          }`}
        >
          {/* Header */}
          <div className="relative bg-gradient-to-br from-purple-600 via-pink-500 to-orange-500 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <MessageCircle size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-white font-bold text-lg">AI Support Copilot</h3>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-white/80 text-xs">Online</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/20"
              aria-label="Close chat"
            >
              <X size={24} />
            </button>
          </div>

          {/* Agent Info Card */}
          <div
            className={`p-4 border-b ${
              isDarkMode ? 'bg-gray-800/50 border-gray-700' : 'bg-purple-50/50 border-gray-200'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="text-4xl">🤖</div>
              <div className="flex-1">
                <h4
                  className={`font-bold text-base mb-1 ${
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  }`}
                >
                  Kgen21 Support Agent
                </h4>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  A helpful assistant agent that provides user support for the Kgen21 app, offering
                  guidance, education, and troubleshooting.
                </p>
              </div>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Welcome Message */}
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">🤖</div>
                <p
                  className={`text-lg font-medium ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}
                >
                  Nice meeting you!
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-br from-purple-600 to-pink-500 text-white'
                      : isDarkMode
                        ? 'bg-gray-800 text-gray-200'
                        : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length === 0 && (
            <div className={`px-4 py-3 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
              <div className="space-y-2">
                {quickQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className={`w-full text-left px-4 py-2.5 rounded-xl text-sm transition-all duration-200 flex items-center gap-2 ${
                      isDarkMode
                        ? 'bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700'
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-200'
                    }`}
                  >
                    <MessageCircle size={16} className="text-purple-500 flex-shrink-0" />
                    <span className="truncate">{question}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className={`p-4 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center gap-2">
              <button
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode
                    ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-300'
                    : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
                }`}
                aria-label="Attach file"
              >
                <Paperclip size={20} />
              </button>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type your message..."
                className={`flex-1 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all ${
                  isDarkMode
                    ? 'bg-gray-800 text-white placeholder-gray-500'
                    : 'bg-gray-100 text-gray-900 placeholder-gray-400'
                }`}
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim()}
                className="p-3 rounded-xl bg-gradient-to-br from-purple-600 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbot;

