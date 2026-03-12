/**
 * Mock data toggle component for switching between mock and production data
 */

import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

interface MockDataToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export const MockDataToggle: React.FC<MockDataToggleProps> = ({ enabled, onToggle }) => {
  const { language } = useLanguage();

  const labels = {
    en: {
      label: 'Demo Mode',
      enabled: 'Using mock data',
      disabled: 'Using live data',
    },
    es: {
      label: 'Modo Demo',
      enabled: 'Usando datos simulados',
      disabled: 'Usando datos en vivo',
    },
  };

  const text = labels[language];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label style={{ fontSize: '14px', fontWeight: '500' }}>
        {text.label}:
      </label>
      <button
        onClick={() => onToggle(!enabled)}
        style={{
          padding: '8px 16px',
          backgroundColor: enabled ? '#10B981' : '#6B7280',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
        }}
      >
        {enabled ? text.enabled : text.disabled}
      </button>
    </div>
  );
};
