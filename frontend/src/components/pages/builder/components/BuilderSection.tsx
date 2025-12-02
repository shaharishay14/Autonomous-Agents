import { useState } from 'react';
import BuilderInput from './BuilderInput';
import CategoryButtons from './CategoryButtons';
import { useGetTemplates } from '../hooks';

function BuilderSection() {
  const [prompt, setPrompt] = useState('');
  
  // שימוש ב-hook לשליפת templates
  const { templates, isLoading } = useGetTemplates();

  const handleTemplateSelect = (templatePrompt: string) => {
    setPrompt(templatePrompt);
  };

  return (
    <>
      <BuilderInput prompt={prompt} setPrompt={setPrompt} />
      <CategoryButtons 
        onTemplateSelect={handleTemplateSelect} 
        categories={templates}
        isLoading={isLoading}
      />
    </>
  );
}

export default BuilderSection;

