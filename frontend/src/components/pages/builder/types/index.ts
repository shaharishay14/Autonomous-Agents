export interface CreateAgentPayload {
  prompt: string;
  name?: string;
  app_connections?: string[];
  avatar?: File | null;
}

export interface CreateAgentResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  // הוסף כאן שדות נוספים בהתאם לתגובה מהשרת
}

export interface FAQItem {
  question: string;
  answer: string;
}

