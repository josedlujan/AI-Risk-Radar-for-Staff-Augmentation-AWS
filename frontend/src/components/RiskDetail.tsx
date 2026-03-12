/**
 * Risk detail component showing detailed analysis and recommendations
 */

import React from 'react';
import { RiskRecord, SeverityLevel } from '../types/models';
import { useLanguage } from '../contexts/LanguageContext';

interface RiskDetailProps {
  risk: RiskRecord;
  onBack: () => void;
}

const severityColors: Record<SeverityLevel, string> = {
  critical: '#DC2626',
  high: '#F59E0B',
  medium: '#3B82F6',
  low: '#10B981',
};

const severityLabels = {
  en: {
    critical: 'CRITICAL',
    high: 'HIGH',
    medium: 'MEDIUM',
    low: 'LOW',
  },
  es: {
    critical: 'CRÍTICO',
    high: 'ALTO',
    medium: 'MEDIO',
    low: 'BAJO',
  },
};

const dimensionLabels = {
  en: {
    delivery_cadence: 'Delivery Cadence',
    knowledge_concentration: 'Knowledge Concentration',
    dependency_risk: 'Dependency Risk',
    workload_distribution: 'Workload Distribution',
    attrition_signal: 'Attrition Signal',
  },
  es: {
    delivery_cadence: 'Cadencia de Entrega',
    knowledge_concentration: 'Concentración de Conocimiento',
    dependency_risk: 'Riesgo de Dependencias',
    workload_distribution: 'Distribución de Carga',
    attrition_signal: 'Señal de Desgaste',
  },
};

export const RiskDetail: React.FC<RiskDetailProps> = ({ risk, onBack }) => {
  const { language } = useLanguage();

  const getDescription = (risk: RiskRecord): string => {
    return language === 'en' ? risk.description_en : risk.description_es;
  };

  const getRecommendations = (risk: RiskRecord): string[] => {
    return language === 'en' ? risk.recommendations_en : risk.recommendations_es;
  };

  const getDimensionLabel = (dimension: string): string => {
    return dimensionLabels[language][dimension as keyof typeof dimensionLabels.en] || dimension;
  };

  const getSeverityLabel = (severity: SeverityLevel): string => {
    return severityLabels[language][severity];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString(language === 'es' ? 'es-ES' : 'en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const labels = {
    en: {
      back: '← Back to Risk List',
      detectedAt: 'Detected at',
      recommendations: 'Recommendations',
    },
    es: {
      back: '← Volver a la Lista de Riesgos',
      detectedAt: 'Detectado el',
      recommendations: 'Recomendaciones',
    },
  };

  const text = labels[language];

  return (
    <div>
      <button
        onClick={onBack}
        style={{
          padding: '8px 16px',
          backgroundColor: '#F3F4F6',
          border: '1px solid #D1D5DB',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          marginBottom: '20px',
        }}
      >
        {text.back}
      </button>

      <div
        style={{
          padding: '24px',
          border: '1px solid #E5E7EB',
          borderRadius: '8px',
          backgroundColor: 'white',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <span
            style={{
              padding: '6px 16px',
              backgroundColor: severityColors[risk.severity],
              color: 'white',
              borderRadius: '4px',
              fontSize: '14px',
              fontWeight: '700',
            }}
          >
            {getSeverityLabel(risk.severity)}
          </span>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600' }}>
            {getDimensionLabel(risk.dimension)}
          </h2>
        </div>

        <p style={{ fontSize: '14px', color: '#6B7280', marginBottom: '8px' }}>
          {text.detectedAt}: {formatDate(risk.detected_at)}
        </p>

        <p style={{ fontSize: '16px', color: '#374151', marginBottom: '24px', lineHeight: '1.6' }}>
          {getDescription(risk)}
        </p>

        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>
            {text.recommendations}
          </h3>
          <ul style={{ paddingLeft: '20px', margin: 0 }}>
            {getRecommendations(risk).map((recommendation, index) => (
              <li
                key={index}
                style={{
                  fontSize: '15px',
                  color: '#374151',
                  marginBottom: '8px',
                  lineHeight: '1.6',
                }}
              >
                {recommendation}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
