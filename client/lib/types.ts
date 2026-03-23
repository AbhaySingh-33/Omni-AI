export type Role = "user" | "assistant";

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  agent?: AgentType;
}

export type AgentType = "reasoning" | "research" | "tools" | "memory" | "router";

export interface AgentInfo {
  id: AgentType;
  label: string;
  description: string;
  color: string;
  icon: string;
}

export interface AuthUser {
  email: string;
  token: string;
}
