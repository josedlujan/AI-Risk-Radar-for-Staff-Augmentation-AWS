/**
 * Radar chart component for visualizing five risk dimensions
 */

import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { RiskDimensionValues } from '../types/models';
import { useLanguage } from '../contexts/LanguageContext';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface RiskRadarChartProps {
  dimensions: RiskDimensionValues;
}

export const RiskRadarChart: React.FC<RiskRadarChartProps> = ({ dimensions }) => {
  const { language } = useLanguage();

  const labels = {
    en: {
      delivery_cadence: 'Delivery Cadence',
      knowledge_concentration: 'Knowledge Concentration',
      dependency_risk: 'Dependency Risk',
      workload_distribution: 'Workload Distribution',
      attrition_signal: 'Attrition Signal',
      title: 'Team Risk Dimensions',
    },
    es: {
      delivery_cadence: 'Cadencia de Entrega',
      knowledge_concentration: 'Concentración de Conocimiento',
      dependency_risk: 'Riesgo de Dependencias',
      workload_distribution: 'Distribución de Carga',
      attrition_signal: 'Señal de Desgaste',
      title: 'Dimensiones de Riesgo del Equipo',
    },
  };

  const text = labels[language];

  const data = {
    labels: [
      text.delivery_cadence,
      text.knowledge_concentration,
      text.dependency_risk,
      text.workload_distribution,
      text.attrition_signal,
    ],
    datasets: [
      {
        label: text.title,
        data: [
          dimensions.delivery_cadence,
          dimensions.knowledge_concentration,
          dimensions.dependency_risk,
          dimensions.workload_distribution,
          dimensions.attrition_signal,
        ],
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(239, 68, 68, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(239, 68, 68, 1)',
      },
    ],
  };

  const options = {
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 20,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div style={{ maxWidth: '500px', margin: '0 auto' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>{text.title}</h2>
      <Radar data={data} options={options} />
    </div>
  );
};
