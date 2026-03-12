/**
 * Risk list component displaying risks with severity badges
 */

import React from 'react';
import { RiskRecord, SeverityLevel } from '../types/models';
import { useLanguage } from '../contexts/LanguageContext';

interface RiskListProps {
  risks: RiskRecord[];
  onRiskClick: (risk: RiskRecord) => void;
}

const severityOrder: Record<SeverityLevel, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

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

export const RiskList: React.FC<RiskListProps> = ({ risks, onRiskClick }) => {
  const { language } = useLanguage();

  const sortedRisks = [...risks].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  const getDescription = (risk: RiskRecord): string => {
    return language === 'en' ? risk.description_en : risk.description_es;
  };

  const getDimensionLabel = (dimension: string): string => {
    return dimensionLabels[language][dimension as keyof typeof dimensionLabels.en] || dimension;
  };

  const getSeverityLabel = (severity: SeverityLevel): string => {
    return severityLabels[language][severity];
  };

  const headers = {
    en: {
      title: 'Detected Risks',
      empty: 'No risks detected',
    },
    es: {
      title: 'Riesgos Detectados',
      empty: 'No se detectaron riesgos',
    },
  };

  const text = headers[language];

  if (risks.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#6B7280' }}>
        {text.empty}
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>{text.title}</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sortedRisks.map((risk) => (
          <div
            key={risk.risk_id}
            onClick={() => onRiskClick(risk)}
            style={{
              padding: '16px',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backgroundColor: 'white',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
              e.currentTarget.style.borderColor = severityColors[risk.severity];
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = 'none';
              e.currentTarget.style.borderColor = '#E5E7EB';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <span
                style={{
                  padding: '4px 12px',
                  backgroundColor: severityColors[risk.severity],
                  color: 'white',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: '700',
                }}
              >
                {getSeverityLabel(risk.severity)}
              </span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#374151' }}>
                {getDimensionLabel(risk.dimension)}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '14px', color: '#6B7280' }}>
              {getDescription(risk)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
