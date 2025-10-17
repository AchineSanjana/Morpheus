export type Msg = {
  role: "user" | "assistant";
  content: string;
  responsibleAIChecks?: Record<string, any>;
  responsibleAIPassed?: boolean;
  responsibleAIRiskLevel?: string;
  data?: Record<string, any>;
  audioId?: string;
};
