import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import useDarkModeStore from '../../../../../store/darkmode.store';
import { categories } from '../../../shared/constants/categories';
import type { Category, Template } from '../../../shared/constants/categories';

interface CategoryButtonsProps {
  onTemplateSelect: (prompt: string) => void;
}

function CategoryButtons({ onTemplateSelect }: CategoryButtonsProps) {
  const { isDarkMode } = useDarkModeStore();
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);

  const handleCategoryClick = (category: Category) => {
    setSelectedCategory(category);
  };

  const handleTemplateClick = (template: Template) => {
    onTemplateSelect(template.prompt);
    setSelectedCategory(null);
  };

  const handleBack = () => {
    setSelectedCategory(null);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <AnimatePresence mode="wait">
        {!selectedCategory ? (
          <motion.div
            key="categories"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <p className={`text-center mb-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Or try one of these:
            </p>
            
            <div className="flex flex-wrap justify-center gap-3 mb-6">
              {categories.map((category, index) => {
                const IconComponent = category.icon;
                return (
                  <motion.button
                    key={index}
                    onClick={() => handleCategoryClick(category)}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all border backdrop-blur-sm ${
                      isDarkMode
                        ? 'bg-gray-800/50 hover:bg-gray-700/70 border-gray-700/50 text-gray-300 hover:text-white'
                        : 'bg-white/60 hover:bg-white/80 border-purple-200 text-gray-700 hover:text-purple-700 shadow-sm hover:shadow-md'
                    }`}
                  >
                    <IconComponent size={18} />
                    <span className="text-sm font-medium">{category.label}</span>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="templates"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className={`p-8 rounded-2xl border backdrop-blur-md ${
              isDarkMode
                ? 'bg-gray-800/50 border-gray-700/50'
                : 'bg-white/60 border-purple-200'
            }`}
          >
            {/* Back Button */}
            <motion.button
              onClick={handleBack}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`flex items-center gap-2 mb-6 px-4 py-2 rounded-lg transition-all ${
                isDarkMode
                  ? 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                  : 'text-gray-600 hover:text-purple-700 hover:bg-purple-50'
              }`}
            >
              <ArrowLeft size={18} />
              <span className="text-sm font-medium">Back to categories</span>
            </motion.button>

            {/* Category Title with Icon */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="flex items-center justify-center gap-3 mb-8"
            >
              {(() => {
                const IconComponent = selectedCategory.icon;
                return <IconComponent size={24} className={isDarkMode ? 'text-purple-400' : 'text-purple-600'} />;
              })()}
              <h3 className={`text-xl font-semibold ${
                isDarkMode ? 'text-gray-200' : 'text-gray-800'
              }`}>
                {selectedCategory.label}
              </h3>
            </motion.div>

            <p className={`text-center mb-6 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Choose a template:
            </p>

            {/* Templates Grid */}
            <div className="flex flex-wrap justify-center gap-3">
              {selectedCategory.templates.map((template, index) => (
                <motion.button
                  key={index}
                  onClick={() => handleTemplateClick(template)}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 + index * 0.08 }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`px-4 py-2 rounded-full transition-all border backdrop-blur-sm font-medium ${
                    isDarkMode
                      ? 'bg-gray-800/50 hover:bg-gray-700/70 border-gray-700/50 text-gray-300 hover:text-white'
                      : 'bg-white/60 hover:bg-white/80 border-purple-200 text-gray-700 hover:text-purple-700 shadow-sm hover:shadow-md'
                  }`}
                >
                  <span className="text-sm">{template.name}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default CategoryButtons;

