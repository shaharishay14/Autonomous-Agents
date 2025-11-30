import { useState } from 'react';
import BuilderInput from './BuilderInput';
import CategoryButtons from './CategoryButtons';

function BuilderSection() {
  const [prompt, setPrompt] = useState('');

  const handleTemplateSelect = (templatePrompt: string) => {
    setPrompt(templatePrompt);
  };

  return (
    <>
      <BuilderInput prompt={prompt} setPrompt={setPrompt} />
      <CategoryButtons onTemplateSelect={handleTemplateSelect} />
    </>
  );
}

export default BuilderSection;

