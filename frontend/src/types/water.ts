/**
 * Water Quality parameter values sent to the FastAPI ML backend.
 */
export interface WaterParameters {
  ph: number;
  Hardness: number;
  Solids: number;
  Chloramines: number;
  Sulfate: number;
  Conductivity: number;
  Organic_carbon: number;
  Trihalomethanes: number;
  Turbidity: number;
}

/**
 * Status evaluation for a single parameter against EPA/WHO guidelines.
 */
export interface ParameterEvaluation {
  parameter: string;
  value: number | null;
  unit: string;
  is_safe: boolean;
  safe_range: string;
  status_message: string;
}

/**
 * Prediction payload returned by /api/predict.
 */
export interface PredictionResponse {
  is_potable: boolean;
  potability_label: string;
  potability_probability: number;
  non_potability_probability: number;
  confidence_score: number;
  water_quality_grade: string;
  parameter_evaluations: ParameterEvaluation[];
  warnings: string[];
  model_name: string;
  model_version: string;
}

/**
 * Metadata for a single feature from /api/metadata.
 */
export interface FeatureMeta {
  name: string;
  unit: string;
  description: string;
  min: number;
  max: number;
  mean: number;
  median: number;
  q25: number;
  q75: number;
  safe_min: number;
  safe_max: number;
  step?: number;
}

/**
 * Complete metadata structure.
 */
export interface ModelMetadata {
  model_name: string;
  primary_metric: string;
  roc_auc: number;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
  };
  features: Record<string, FeatureMeta>;
  feature_order: string[];
}
