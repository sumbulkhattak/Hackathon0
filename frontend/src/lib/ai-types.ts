// ── AI Employee Dashboard Types ──

export interface QueueCounts {
  Needs_Action: number;
  Pending_Approval: number;
  Approved: number;
  Rejected: number;
  Plans: number;
}

export interface TodayActivity {
  date: string;
  total_entries: number;
  by_action: Record<string, number>;
  by_entity_type: Record<string, number>;
  by_status: Record<string, number>;
  completed: number;
  pending: number;
  errors: number;
  orders: number;
  inquiries: number;
  alerts: number;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  source: string;
  action: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  details: Record<string, unknown>;
  queue: string;
  status: string;
  duration_ms: number | null;
  error: string | null;
}

export interface SystemHealth {
  status: string;
  components: Record<string, string>;
}

export interface DashboardResponse {
  queue_counts: QueueCounts;
  today_activity: TodayActivity;
  recent_actions: AuditEntry[];
  watchers: { filename: string; slug: string }[];
  db_stats: {
    total_orders: number;
    total_revenue: number;
    total_products: number;
    low_stock_count: number;
  };
  system_health: SystemHealth;
}

// ── Tasks ──

export interface TaskSummary {
  filename: string;
  queue: string;
  task_type: string;
  timestamp_str: string;
  size: number;
  modified: string;
}

export interface TaskDetail {
  filename: string;
  queue: string;
  metadata: Record<string, string>;
  content: string;
}

export interface TaskListResponse {
  count: number;
  tasks: TaskSummary[];
}

// ── Audit ──

export interface AuditListResponse {
  count: number;
  entries: AuditEntry[];
}

// ── Memory ──

export interface MemoryFile {
  filename: string;
  slug: string;
  size: number;
  modified: string;
}

export interface MemoryListResponse {
  count: number;
  clients?: MemoryFile[];
  files?: MemoryFile[];
  projects?: MemoryFile[];
}

export interface MemoryContentResponse {
  slug?: string;
  filename: string;
  content: string;
}
