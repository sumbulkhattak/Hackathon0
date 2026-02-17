import type {
  DashboardResponse,
  TaskListResponse,
  TaskDetail,
  AuditListResponse,
  TodayActivity,
  MemoryListResponse,
  MemoryContentResponse,
} from "./ai-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAI(endpoint: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ── Dashboard ──

export async function getDashboard(): Promise<DashboardResponse> {
  return fetchAI("/api/dashboard");
}

// ── Tasks ──

export async function getTasks(filters?: {
  queue?: string;
  type?: string;
  priority?: string;
}): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  if (filters?.queue) params.append("queue", filters.queue);
  if (filters?.type) params.append("type", filters.type);
  if (filters?.priority) params.append("priority", filters.priority);
  const query = params.toString();
  return fetchAI(`/api/tasks${query ? `?${query}` : ""}`);
}

export async function getTask(taskId: string): Promise<TaskDetail> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}`);
}

export async function processTask(taskId: string): Promise<unknown> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}/process`, {
    method: "POST",
  });
}

export async function approveTask(
  taskId: string,
  approvedBy?: string
): Promise<unknown> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved_by: approvedBy || "admin" }),
  });
}

export async function rejectTask(
  taskId: string,
  rejectedBy?: string,
  reason?: string
): Promise<unknown> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}/reject`, {
    method: "POST",
    body: JSON.stringify({
      rejected_by: rejectedBy || "admin",
      reason: reason || "Rejected via dashboard",
    }),
  });
}

export async function reprocessTask(taskId: string): Promise<unknown> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}/reprocess`, {
    method: "POST",
  });
}

export async function executeTask(
  taskId: string,
  executedBy: string,
  notes?: string
): Promise<unknown> {
  return fetchAI(`/api/tasks/${encodeURIComponent(taskId)}/execute`, {
    method: "POST",
    body: JSON.stringify({ executed_by: executedBy, notes }),
  });
}

export async function deleteTask(
  taskId: string,
  queue: string
): Promise<unknown> {
  return fetchAI(
    `/api/tasks/${encodeURIComponent(taskId)}?queue=${encodeURIComponent(queue)}`,
    { method: "DELETE" }
  );
}

// ── Audit ──

export async function getAuditEntries(filters?: {
  date?: string;
  action?: string;
  type?: string;
}): Promise<AuditListResponse> {
  const params = new URLSearchParams();
  if (filters?.date) params.append("date", filters.date);
  if (filters?.action) params.append("action", filters.action);
  if (filters?.type) params.append("type", filters.type);
  const query = params.toString();
  return fetchAI(`/api/audit${query ? `?${query}` : ""}`);
}

export async function getAuditToday(): Promise<TodayActivity> {
  return fetchAI("/api/audit/today");
}

// ── Memory ──

export async function getMemoryClients(): Promise<MemoryListResponse> {
  return fetchAI("/api/memory/clients");
}

export async function getMemoryClient(
  slug: string
): Promise<MemoryContentResponse> {
  return fetchAI(`/api/memory/clients/${encodeURIComponent(slug)}`);
}

export async function getMemoryFinance(): Promise<MemoryListResponse> {
  return fetchAI("/api/memory/finance");
}

export async function getMemoryFinanceFile(
  name: string
): Promise<MemoryContentResponse> {
  return fetchAI(`/api/memory/finance/${encodeURIComponent(name)}`);
}

export async function getMemoryProjects(): Promise<MemoryListResponse> {
  return fetchAI("/api/memory/projects");
}

export async function getMemoryProject(
  slug: string
): Promise<MemoryContentResponse> {
  return fetchAI(`/api/memory/projects/${encodeURIComponent(slug)}`);
}

// ── E-Commerce ──

export async function triggerProduct(data: {
  name: string;
  description: string;
  price: number;
  category_id: number;
  stock?: number;
  featured?: boolean;
}): Promise<unknown> {
  return fetchAI("/trigger/product", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function triggerPriceUpdate(data: {
  product_id: number;
  new_price: number;
  reason: string;
}): Promise<unknown> {
  return fetchAI("/trigger/price-update", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getEcommerceStats(): Promise<{
  products: { total: number; low_stock: number; out_of_stock: number };
  orders: { total: number; pending: number; completed: number; revenue: number };
  inquiries: { pending: number; awaiting_response: number };
}> {
  return fetchAI("/api/ecommerce/stats");
}
