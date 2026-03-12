/**
 * API client for Team Risk Analysis System
 */

import {
  RisksResponse,
  IngestRequest,
  IngestResponse,
  AnalyzeRequest,
  AnalyzeResponse,
} from '../types/models';

export class RiskAnalysisAPI {
  private baseUrl: string;
  private useMockData: boolean = false;

  constructor(baseUrl: string = import.meta.env.VITE_API_URL || '/api') {
    this.baseUrl = baseUrl;
  }

  setMockDataMode(enabled: boolean): void {
    this.useMockData = enabled;
  }

  async fetchRisks(teamId: string, language: 'en' | 'es' = 'en'): Promise<RisksResponse> {
    try {
      const endpoint = this.useMockData
        ? `${this.baseUrl}/mock-data?team_id=${teamId}&language=${language}`
        : `${this.baseUrl}/risks?team_id=${teamId}&language=${language}`;

      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching risks:', error);
      throw error;
    }
  }

  async submitSignals(request: IngestRequest): Promise<IngestResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/signals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting signals:', error);
      throw error;
    }
  }

  async triggerAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error triggering analysis:', error);
      throw error;
    }
  }

  async fetchMockData(scenario: string = 'overloaded'): Promise<RisksResponse> {
    // Generate mock data locally for demo purposes
    const mockData: RisksResponse = {
      team_id: 'demo-team-001',
      last_analysis: new Date().toISOString(),
      risk_dimensions: {
        delivery_cadence: 75.0,
        knowledge_concentration: 55.0,
        dependency_risk: 60.0,
        workload_distribution: 85.0,
        attrition_signal: 70.0,
      },
      risks: [
        {
          risk_id: 'risk-001',
          analysis_id: 'analysis-001',
          team_id: 'demo-team-001',
          dimension: 'workload_distribution',
          severity: 'critical',
          detected_at: new Date().toISOString(),
          description_en: 'Severe workload imbalance detected with team members significantly overloaded',
          description_es: 'Se detectó un desequilibrio severo de carga de trabajo con miembros del equipo significativamente sobrecargados',
          recommendations_en: [
            'Immediately redistribute tasks to balance workload',
            'Consider bringing in additional resources',
            'Postpone non-critical features',
            'Review and adjust sprint commitments',
          ],
          recommendations_es: [
            'Redistribuir inmediatamente las tareas para equilibrar la carga de trabajo',
            'Considerar traer recursos adicionales',
            'Posponer características no críticas',
            'Revisar y ajustar los compromisos del sprint',
          ],
          signal_values: {
            delivery_cadence: 75.0,
            knowledge_concentration: 55.0,
            dependency_risk: 60.0,
            workload_distribution: 85.0,
            attrition_signal: 70.0,
          },
        },
        {
          risk_id: 'risk-002',
          analysis_id: 'analysis-001',
          team_id: 'demo-team-001',
          dimension: 'delivery_cadence',
          severity: 'high',
          detected_at: new Date().toISOString(),
          description_en: 'Delivery velocity declining due to excessive workload',
          description_es: 'La velocidad de entrega está disminuyendo debido a la carga de trabajo excesiva',
          recommendations_en: [
            'Reduce scope of current sprint',
            'Focus on completing in-progress work',
            'Limit work-in-progress items',
          ],
          recommendations_es: [
            'Reducir el alcance del sprint actual',
            'Enfocarse en completar el trabajo en progreso',
            'Limitar los elementos de trabajo en progreso',
          ],
          signal_values: {
            delivery_cadence: 75.0,
            knowledge_concentration: 55.0,
            dependency_risk: 60.0,
            workload_distribution: 85.0,
            attrition_signal: 70.0,
          },
        },
        {
          risk_id: 'risk-003',
          analysis_id: 'analysis-001',
          team_id: 'demo-team-001',
          dimension: 'attrition_signal',
          severity: 'high',
          detected_at: new Date().toISOString(),
          description_en: 'High attrition risk due to sustained overwork',
          description_es: 'Alto riesgo de desgaste debido al exceso de trabajo sostenido',
          recommendations_en: [
            'Address burnout concerns immediately',
            'Ensure team takes time off',
            'Review workload expectations with leadership',
          ],
          recommendations_es: [
            'Abordar las preocupaciones de agotamiento inmediatamente',
            'Asegurar que el equipo tome tiempo libre',
            'Revisar las expectativas de carga de trabajo con el liderazgo',
          ],
          signal_values: {
            delivery_cadence: 75.0,
            knowledge_concentration: 55.0,
            dependency_risk: 60.0,
            workload_distribution: 85.0,
            attrition_signal: 70.0,
          },
        },
        {
          risk_id: 'risk-004',
          analysis_id: 'analysis-001',
          team_id: 'demo-team-001',
          dimension: 'dependency_risk',
          severity: 'medium',
          detected_at: new Date().toISOString(),
          description_en: 'Dependencies causing delays in overloaded environment',
          description_es: 'Las dependencias están causando retrasos en un entorno sobrecargado',
          recommendations_en: [
            'Identify and resolve blocking dependencies',
            'Improve cross-team communication',
          ],
          recommendations_es: [
            'Identificar y resolver dependencias bloqueantes',
            'Mejorar la comunicación entre equipos',
          ],
          signal_values: {
            delivery_cadence: 75.0,
            knowledge_concentration: 55.0,
            dependency_risk: 60.0,
            workload_distribution: 85.0,
            attrition_signal: 70.0,
          },
        },
      ],
      is_mock_data: true,
    };

    return Promise.resolve(mockData);
  }
}
