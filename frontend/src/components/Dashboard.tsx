/**
 * Main Dashboard component integrating all risk analysis components
 */

import React, { useState, useEffect } from 'react';
import { RiskAnalysisAPI } from '../api/RiskAnalysisAPI';
import { RiskRecord, RisksResponse } from '../types/models';
import { RiskRadarChart } from './RiskRadarChart';
import { RiskList } from './RiskList';
import { RiskDetail } from './RiskDetail';
import { LanguageToggle } from './LanguageToggle';
import { MockDataToggle } from './MockDataToggle';
import { useLanguage } from '../contexts/LanguageContext';

const api = new RiskAnalysisAPI();

export const Dashboard: React.FC = () => {
  const { language } = useLanguage();
  const [data, setData] = useState<RisksResponse | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<RiskRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [mockDataEnabled, setMockDataEnabled] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, [language, mockDataEnabled]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      api.setMockDataMode(mockDataEnabled);
      const response = mockDataEnabled
        ? await api.fetchMockData()
        : await api.fetchRisks('demo-team-001', language);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMockDataToggle = (enabled: boolean) => {
    setMockDataEnabled(enabled);
    setSelectedRisk(null);
  };

  const handleRiskClick = (risk: RiskRecord) => {
    setSelectedRisk(risk);
  };

  const handleBack = () => {
    setSelectedRisk(null);
  };

  const labels = {
    en: {
      title: 'Team Risk Analysis Dashboard',
      loading: 'Loading...',
      error: 'Error loading data',
      retry: 'Retry',
      mockIndicator: '🎭 Demo Mode - Using simulated data',
      lastAnalysis: 'Last Analysis',
    },
    es: {
      title: 'Panel de Análisis de Riesgos del Equipo',
      loading: 'Cargando...',
      error: 'Error al cargar datos',
      retry: 'Reintentar',
      mockIndicator: '🎭 Modo Demo - Usando datos simulados',
      lastAnalysis: 'Último Análisis',
    },
  };

  const text = labels[language];

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ fontSize: '18px', color: '#6B7280' }}>{text.loading}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p style={{ fontSize: '18px', color: '#DC2626', marginBottom: '16px' }}>
          {text.error}: {error}
        </p>
        <button
          onClick={loadData}
          style={{
            padding: '8px 16px',
            backgroundColor: '#4A90E2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          {text.retry}
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F9FAFB', padding: '20px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '24px',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <h1 style={{ margin: 0, fontSize: '28px', fontWeight: '700', color: '#111827' }}>
            {text.title}
          </h1>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <MockDataToggle enabled={mockDataEnabled} onToggle={handleMockDataToggle} />
            <LanguageToggle />
          </div>
        </div>

        {/* Mock Data Indicator */}
        {data.is_mock_data && (
          <div
            style={{
              padding: '12px 16px',
              backgroundColor: '#FEF3C7',
              border: '1px solid #FCD34D',
              borderRadius: '8px',
              marginBottom: '24px',
              fontSize: '14px',
              color: '#92400E',
            }}
          >
            {text.mockIndicator}
          </div>
        )}

        {/* Last Analysis Timestamp */}
        <p style={{ fontSize: '14px', color: '#6B7280', marginBottom: '24px' }}>
          {text.lastAnalysis}: {new Date(data.last_analysis).toLocaleString(language === 'es' ? 'es-ES' : 'en-US')}
        </p>

        {/* Main Content */}
        {selectedRisk ? (
          <RiskDetail risk={selectedRisk} onBack={handleBack} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* Left Column: Radar Chart */}
            <div
              style={{
                padding: '24px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              }}
            >
              <RiskRadarChart dimensions={data.risk_dimensions} />
            </div>

            {/* Right Column: Risk List */}
            <div
              style={{
                padding: '24px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              }}
            >
              <RiskList risks={data.risks} onRiskClick={handleRiskClick} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
