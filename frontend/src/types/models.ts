/**
 * TypeScript interfaces for Team Risk Analysis System frontend data models.
 */

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';

export type RiskDimension = 
  | 'delivery_cadence'
  | 'knowledge_concentration'
  | 'dependency_risk'
  | 'workload_distribution'
  | 'attrition_signal';

export interface SignalMetadata {
  team_size: number;
  project_count: number;
  aggregation_period: string;
}

export interface TeamSignal {
  team_id: string;
  timestamp: string;
  delivery_cadence: number;
  knowledge_concentration: number;
  dependency_risk: number;
  workload_distribution: number;
  attrition_signal: number;
  metadata: SignalMetadata;
}

export interface RiskRecord {
  risk_id: string;
  analysis_id: string;
  team_id: string;
  dimension: RiskDimension;
  severity: SeverityLevel;
  detected_at: string;
  description_en: string;
  description_es: string;
  recommendations_en: string[];
  recommendations_es: string[];
  signal_values: Record<RiskDimension, number>;
}

export interface RiskDimensionValues {
  delivery_cadence: number;
  knowledge_concentration: number;
  dependency_risk: number;
  workload_distribution: number;
  attrition_signal: number;
}

export interface RisksResponse {
  team_id: string;
  last_analysis: string;
  risk_dimensions: RiskDimensionValues;
  risks: RiskRecord[];
  is_mock_data?: boolean;
}

export interface SnapshotRisk {
  risk_id: string;
  dimension: RiskDimension;
  severity: SeverityLevel;
  description_en: string;
  description_es: string;
}

export interface SnapshotMetadata {
  team_size: number;
  project_count: number;
  analysis_duration_ms: number;
}

export interface Snapshot {
  snapshot_id: string;
  team_id: string;
  timestamp: string;
  signals: RiskDimensionValues;
  risks: SnapshotRisk[];
  metadata: SnapshotMetadata;
}

export interface IngestRequest {
  team_id: string;
  timestamp: string;
  signals: RiskDimensionValues;
  metadata: SignalMetadata;
}

export interface IngestResponse {
  status: 'success' | 'error';
  signal_id?: string;
  message: string;
}

export interface AnalyzeRequest {
  team_id: string;
  analysis_type: 'scheduled' | 'on_demand';
}

export interface AnalyzeResponse {
  status: 'success' | 'error';
  analysis_id?: string;
  risks_detected?: number;
  snapshot_url?: string;
  message?: string;
}
