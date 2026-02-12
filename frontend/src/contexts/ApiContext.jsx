import React, { createContext, useContext, useState } from 'react';

const ApiContext = createContext();

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

export const ApiProvider = ({ children }) => {
  const [apiKeys, setApiKeys] = useState({
    ollama_url: localStorage.getItem('ollama_url') || 'http://localhost:11434',
    ollama_model: localStorage.getItem('ollama_model') || 'llama3'
  });

  const [apiStatus, setApiStatus] = useState({
    ollama: false
  });

  const updateApiKey = (service, key) => {
    setApiKeys((prev) => ({ ...prev, [service]: key }));
    localStorage.setItem(service, key);
  };

  const clearApiKeys = () => {
    setApiKeys({ ollama_url: 'http://localhost:11434', ollama_model: 'llama3' });
    localStorage.removeItem('ollama_url');
    localStorage.removeItem('ollama_model');
  };

  return (
    <ApiContext.Provider value={{ apiKeys, apiStatus, setApiStatus, updateApiKey, clearApiKeys }}>
      {children}
    </ApiContext.Provider>
  );
};
