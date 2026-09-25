export interface IncidentMetadata {
  incident_id: string;
  name: string;
  category: string;
  severity: string;
  affected_service: string;
  description: string;
}

export interface MetricScore {
  metric_name: string;
  score: number;
  passed: boolean;
  details?: Record<string, any>;
  explanation?: string;
}

export interface DiagnosisResult {
  incident_id: string;
  root_cause: string;
  root_cause_category?: string;
  suspected_component?: string;
  introduced_by?: string;
  affected_service?: string;
  explanation: string;
  cited_evidence_ids: string[];
  confidence: number;
  recommended_fix?: string;
  usage_metadata?: Record<string, any>;
}

export interface EvaluationReport {
  report_id: string;
  incident_id: string;
  system_name: string;
  timestamp: string;
  root_cause_score: MetricScore;
  introduced_by_score: MetricScore;
  service_score: MetricScore;
  evidence_recall_score: MetricScore;
  evidence_precision_score: MetricScore;
  hallucination_score: MetricScore;
  overall_score: number;
  latency_seconds: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  estimated_cost_usd?: number;
  diagnosis?: DiagnosisResult;
  summary: string;
}

export interface TimelineEvent {
  event_id: string;
  timestamp: string;
  type: string;
  service: string;
  summary: string;
  evidence_ids: string[];
}

export interface Hypothesis {
  hypothesis_id: string;
  hypothesis: string;
  suspected_component?: string;
  suspected_trigger?: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  missing_evidence: string[];
  is_causal: boolean;
  confidence: number;
  rank: number;
}

export interface HypothesisChallenge {
  hypothesis_id: string;
  passed_verification: boolean;
  temporal_ordering_valid: boolean;
  temporal_ordering_notes: string;
  causal_claims_supported: boolean;
  causal_support_notes: string;
  contradictions_detected: string[];
  missing_critical_evidence: string[];
  challenge_notes: string;
}

export interface AgentSteps {
  investigator?: {
    incident_id: string;
    alert_description: string;
    relevant_evidence_ids: string[];
    timeline_events: TimelineEvent[];
    important_entities: Array<{ entity_id: string; name: string; type: string; role?: string }>;
    relevant_relationships: Array<{ edge_id: string; source_id: string; target_id: string; type: string }>;
    observations: Array<{ observation_id: string; statement: string; cited_evidence_ids: string[] }>;
  };
  analyst?: {
    incident_id: string;
    hypotheses: Hypothesis[];
    correlation_vs_causation_notes: string;
    analysis_summary: string;
  };
  verifier?: {
    incident_id: string;
    verdict: string;
    challenges: HypothesisChallenge[];
    best_hypothesis?: Hypothesis;
    verification_summary: string;
  };
}

export interface BenchmarkSystemSummary {
  system_name: string;
  total_incidents: number;
  passed_evaluations: number;
  failed_evaluations: number;
  mean_overall_score: number;
  mean_root_cause_accuracy: number;
  top_3_hypothesis_accuracy: number;
  mean_evidence_recall: number;
  mean_evidence_precision: number;
  hallucination_rate: number;
  false_positive_rate: number;
  verification_success_rate: number;
  mean_latency_seconds: number;
}

export interface LLMTrace {
  trace_id: string;
  incident_id?: string;
  agent_name: string;
  model: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  status: string;
  retries_attempted: number;
  error_message?: string;
}
