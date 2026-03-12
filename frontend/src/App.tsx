/**
 * Main App component
 */

import React from 'react';
import { LanguageProvider } from './contexts/LanguageContext';
import { Dashboard } from './components/Dashboard';

const App: React.FC = () => {
  return (
    <LanguageProvider>
      <Dashboard />
    </LanguageProvider>
  );
};

export default App;
