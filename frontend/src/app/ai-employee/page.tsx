"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  getDashboard,
  getTasks,
  getTask,
  processTask,
  approveTask,
  rejectTask,
  reprocessTask,
  executeTask,
  deleteTask,
  getAuditEntries,
  getMemoryClients,
  getMemoryClient,
  getMemoryFinance,
  getMemoryFinanceFile,
  getMemoryProjects,
  getMemoryProject,
} from "@/lib/ai-api";
import type {
  DashboardResponse,
  TaskSummary,
  TaskDetail,
  AuditEntry,
  MemoryFile,
} from "@/lib/ai-types";

type Tab = "overview" | "tasks" | "activity" | "memory";
type MemoryTab = "clients" | "finance" | "projects";

const BRAND = {
  rose: "#B76E79",
  roseDark: "#8B4F57",
  roseLight: "#D4A0A7",
  blush: "#F9E4E4",
  beige: "#F5F0EB",
  cream: "#FFF8F0",
  dark: "#2D2D2D",
};

const QUEUES = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Executing", "Archived", "Plans"] as const;

const tabs: { key: Tab; icon: string; label: string }[] = [
  { key: "overview", icon: "📊", label: "Overview" },
  { key: "tasks", icon: "📋", label: "Task Queue" },
  { key: "activity", icon: "📜", label: "Activity Log" },
  { key: "memory", icon: "🧠", label: "Memory" },
];

// ════════════════════════════════════════════════════════════════
// Page
// ════════════════════════════════════════════════════════════════

export default function AIEmployeePage() {
  const [tab, setTab] = useState<Tab>("overview");

  // ── Overview state ──
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loadingDash, setLoadingDash] = useState(true);

  // ── Tasks state ──
  const [taskList, setTaskList] = useState<TaskSummary[]>([]);
  const [taskCount, setTaskCount] = useState(0);
  const [taskLoading, setTaskLoading] = useState(false);
  const [filterQueue, setFilterQueue] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [selectedTask, setSelectedTask] = useState<TaskDetail | null>(null);
  const [slideOpen, setSlideOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // ── Audit state ──
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditDate, setAuditDate] = useState("");
  const [auditAction, setAuditAction] = useState("");
  const [auditType, setAuditType] = useState("");

  // ── Memory state ──
  const [memTab, setMemTab] = useState<MemoryTab>("clients");
  const [memFiles, setMemFiles] = useState<MemoryFile[]>([]);
  const [memContent, setMemContent] = useState("");
  const [memSelected, setMemSelected] = useState("");
  const [memLoading, setMemLoading] = useState(false);

  // ── Data loaders ──

  const loadDashboard = useCallback(async () => {
    setLoadingDash(true);
    try {
      const data = await getDashboard();
      setDashboard(data);
    } catch {
      /* silent */
    } finally {
      setLoadingDash(false);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    setTaskLoading(true);
    try {
      const data = await getTasks({
        queue: filterQueue || undefined,
        type: filterType || undefined,
        priority: filterPriority || undefined,
      });
      setTaskList(data.tasks);
      setTaskCount(data.count);
    } catch {
      /* silent */
    } finally {
      setTaskLoading(false);
    }
  }, [filterQueue, filterType, filterPriority]);

  const loadAudit = useCallback(async () => {
    setAuditLoading(true);
    try {
      const data = await getAuditEntries({
        date: auditDate || undefined,
        action: auditAction || undefined,
        type: auditType || undefined,
      });
      setAuditEntries(data.entries);
    } catch {
      /* silent */
    } finally {
      setAuditLoading(false);
    }
  }, [auditDate, auditAction, auditType]);

  const loadMemoryList = useCallback(async () => {
    setMemLoading(true);
    setMemContent("");
    setMemSelected("");
    try {
      if (memTab === "clients") {
        const data = await getMemoryClients();
        setMemFiles(data.clients || []);
      } else if (memTab === "finance") {
        const data = await getMemoryFinance();
        setMemFiles(data.files || []);
      } else {
        const data = await getMemoryProjects();
        setMemFiles(data.projects || []);
      }
    } catch {
      setMemFiles([]);
    } finally {
      setMemLoading(false);
    }
  }, [memTab]);

  const loadMemoryContent = async (slug: string) => {
    setMemSelected(slug);
    try {
      let data;
      if (memTab === "clients") data = await getMemoryClient(slug);
      else if (memTab === "finance") data = await getMemoryFinanceFile(slug);
      else data = await getMemoryProject(slug);
      setMemContent(data.content);
    } catch {
      setMemContent("Failed to load content.");
    }
  };

  // ── Effects ──

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    if (tab === "tasks") loadTasks();
  }, [tab, loadTasks]);

  useEffect(() => {
    if (tab === "activity") loadAudit();
  }, [tab, loadAudit]);

  useEffect(() => {
    if (tab === "memory") loadMemoryList();
  }, [tab, loadMemoryList]);

  // ── Task actions ──

  const handleTaskAction = async (
    action: "process" | "approve" | "reject" | "reprocess" | "execute" | "delete",
    task: TaskSummary
  ) => {
    setActionLoading(task.filename);
    try {
      switch (action) {
        case "process":
          await processTask(task.filename);
          break;
        case "approve":
          await approveTask(task.filename);
          break;
        case "reject":
          await rejectTask(task.filename);
          break;
        case "reprocess":
          await reprocessTask(task.filename);
          break;
        case "execute":
          await executeTask(task.filename, "admin");
          break;
        case "delete":
          await deleteTask(task.filename, task.queue);
          break;
      }
      await loadTasks();
      if (dashboard) loadDashboard();
    } catch {
      /* silent */
    } finally {
      setActionLoading(null);
    }
  };

  const openSlideOver = async (filename: string) => {
    try {
      const detail = await getTask(filename);
      setSelectedTask(detail);
      setSlideOpen(true);
    } catch {
      /* silent */
    }
  };

  // ── Queue counts helper ──
  const qc = dashboard?.queue_counts;
  const needsAction = qc?.Needs_Action ?? 0;
  const pendingApproval = qc?.Pending_Approval ?? 0;
  const approved = qc?.Approved ?? 0;
  const rejected = qc?.Rejected ?? 0;

  // ════════════════════════════════════════════════════════════════
  // Render
  // ════════════════════════════════════════════════════════════════

  return (
    <div className="bg-beige/30 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold text-dark">
            AI Employee
          </h1>
          <p className="text-dark/50 mt-1">
            Task pipeline, audit trail &amp; memory — one control center.
          </p>
        </motion.div>

        {/* ── Tab Navigation ── */}
        <div className="flex gap-1 mb-8 bg-white rounded-2xl p-1.5 shadow-[0_2px_12px_rgba(183,110,121,0.08)] w-fit overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 whitespace-nowrap ${
                tab === t.key
                  ? "bg-rose-gold text-white shadow-[0_4px_12px_rgba(183,110,121,0.3)]"
                  : "text-dark/50 hover:text-dark hover:bg-beige/50"
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Content ── */}
        <AnimatePresence mode="wait">
          {/* ═══════════ OVERVIEW ═══════════ */}
          {tab === "overview" && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {loadingDash ? (
                <LoadingSpinner />
              ) : dashboard ? (
                <>
                  {/* Stat cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                    <StatCard
                      label="System Status"
                      value={dashboard.system_health.status}
                      subtitle="All components"
                      icon="⚡"
                      trend={
                        Object.values(dashboard.system_health.components).every(
                          (c) => c === "ONLINE"
                        )
                          ? "All Online"
                          : "Degraded"
                      }
                      trendUp={Object.values(
                        dashboard.system_health.components
                      ).every((c) => c === "ONLINE")}
                      gradient="from-green-50/40 to-emerald-50/20"
                      iconBg="bg-green-100"
                    />
                    <StatCard
                      label="Needs Action"
                      value={String(needsAction)}
                      subtitle="Awaiting AI processing"
                      icon="🔔"
                      trend={needsAction > 0 ? `${needsAction} pending` : "Clear"}
                      trendUp={needsAction === 0}
                      gradient="from-amber-50/40 to-yellow-50/20"
                      iconBg="bg-amber-100"
                    />
                    <StatCard
                      label="Pending Approval"
                      value={String(pendingApproval)}
                      subtitle="Ready for review"
                      icon="⏳"
                      trend={
                        pendingApproval > 0
                          ? `${pendingApproval} waiting`
                          : "Clear"
                      }
                      trendUp={pendingApproval === 0}
                      gradient="from-blue-50/40 to-indigo-50/20"
                      iconBg="bg-blue-100"
                    />
                    <StatCard
                      label="Completed Today"
                      value={String(dashboard.today_activity.completed)}
                      subtitle={`of ${dashboard.today_activity.total_entries} total events`}
                      icon="✅"
                      trend={`${dashboard.today_activity.completed} done`}
                      trendUp={true}
                      gradient="from-rose-50/40 to-pink-50/20"
                      iconBg="bg-rose-100"
                    />
                  </div>

                  {/* Queue Pipeline */}
                  <QueuePipeline
                    needsAction={needsAction}
                    pendingApproval={pendingApproval}
                    approved={approved}
                    rejected={rejected}
                  />

                  {/* Two-column: metrics + health */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    {/* Today's metrics */}
                    <ChartCard title="Today's Metrics" subtitle={dashboard.today_activity.date}>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { label: "Total Events", value: dashboard.today_activity.total_entries, color: "text-dark" },
                          { label: "Completed", value: dashboard.today_activity.completed, color: "text-green-600" },
                          { label: "Pending", value: dashboard.today_activity.pending, color: "text-amber-600" },
                          { label: "Orders", value: dashboard.today_activity.orders, color: "text-blue-600" },
                          { label: "Inquiries", value: dashboard.today_activity.inquiries, color: "text-purple-600" },
                          { label: "Alerts", value: dashboard.today_activity.alerts, color: "text-orange-600" },
                          { label: "Errors", value: dashboard.today_activity.errors, color: "text-red-600" },
                        ].map((m) => (
                          <div
                            key={m.label}
                            className="flex items-center justify-between py-2 border-b border-blush/30 last:border-0"
                          >
                            <span className="text-sm text-dark/50">{m.label}</span>
                            <span className={`text-sm font-semibold ${m.color}`}>
                              {m.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </ChartCard>

                    {/* System Health */}
                    <ChartCard
                      title="System Components"
                      subtitle={dashboard.system_health.status}
                    >
                      <div className="space-y-3">
                        {Object.entries(dashboard.system_health.components).map(
                          ([name, status]) => (
                            <div
                              key={name}
                              className="flex items-center justify-between py-2 border-b border-blush/30 last:border-0"
                            >
                              <span className="text-sm text-dark/70 capitalize">
                                {name.replace(/_/g, " ")}
                              </span>
                              <span className="flex items-center gap-2 text-xs font-semibold">
                                <span
                                  className={`w-2 h-2 rounded-full ${
                                    status === "ONLINE"
                                      ? "bg-green-500"
                                      : "bg-red-500"
                                  }`}
                                />
                                {status}
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    </ChartCard>
                  </div>

                  {/* Recent Activity */}
                  <ChartCard
                    title="Recent Activity"
                    subtitle="Last actions from audit trail"
                  >
                    {dashboard.recent_actions.length === 0 ? (
                      <EmptyState icon="📭" message="No recent activity" />
                    ) : (
                      <div className="space-y-2">
                        {dashboard.recent_actions.slice(0, 5).map((entry, i) => (
                          <motion.div
                            key={entry.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="flex items-center justify-between py-2.5 border-b border-blush/20 last:border-0"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <span className="text-lg">
                                {actionIcon(entry.action)}
                              </span>
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-dark truncate">
                                  {entry.action}
                                </p>
                                <p className="text-xs text-dark/40 truncate">
                                  {entry.entity_type} · {entry.entity_id}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              <AIStatusBadge status={entry.status} />
                              <span className="text-xs text-dark/30">
                                {formatTime(entry.timestamp)}
                              </span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </ChartCard>
                </>
              ) : (
                <EmptyState
                  icon="⚠️"
                  message="Could not load dashboard. Is the backend running?"
                />
              )}
            </motion.div>
          )}

          {/* ═══════════ TASK QUEUE ═══════════ */}
          {tab === "tasks" && (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {/* Mini-stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <MiniStat label="All Tasks" value={taskCount} color="text-dark" />
                <MiniStat
                  label="Needs Action"
                  value={taskList.filter((t) => t.queue === "Needs_Action").length}
                  color="text-amber-600"
                />
                <MiniStat
                  label="Pending Approval"
                  value={taskList.filter((t) => t.queue === "Pending_Approval").length}
                  color="text-blue-600"
                />
                <MiniStat
                  label="Rejected"
                  value={taskList.filter((t) => t.queue === "Rejected").length}
                  color="text-red-600"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-wrap gap-3 mb-6">
                <select
                  value={filterQueue}
                  onChange={(e) => setFilterQueue(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                >
                  <option value="">All Queues</option>
                  {QUEUES.map((q) => (
                    <option key={q} value={q}>
                      {q.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                >
                  <option value="">All Types</option>
                  {["ORDER", "INQUIRY", "ALERT", "REPORT"].map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                >
                  <option value="">All Priorities</option>
                  {["HIGH", "MEDIUM", "LOW"].map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
                <button
                  onClick={loadTasks}
                  className="px-4 py-2 text-sm font-medium bg-rose-gold text-white rounded-xl hover:bg-rose-gold/90 transition-colors"
                >
                  Refresh
                </button>
              </div>

              {/* Task list */}
              {taskLoading ? (
                <LoadingSpinner />
              ) : taskList.length === 0 ? (
                <EmptyState icon="📭" message="No tasks match the current filters" />
              ) : (
                <div className="space-y-3">
                  {taskList.map((task, i) => (
                    <motion.div
                      key={task.filename}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(183,110,121,0.06)] p-5 hover:shadow-[0_4px_24px_rgba(183,110,121,0.12)] transition-shadow duration-300"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-dark truncate">
                            {task.filename}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 mt-1.5">
                            <AIStatusBadge status={task.queue} />
                            <span className="text-xs text-dark/40">
                              {task.task_type}
                            </span>
                            <span className="text-xs text-dark/30">
                              {formatTime(task.modified)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {/* Queue-specific actions */}
                          {task.queue === "Needs_Action" && (
                            <ActionBtn
                              label="Process"
                              color="bg-amber-500 hover:bg-amber-600"
                              loading={actionLoading === task.filename}
                              onClick={() => handleTaskAction("process", task)}
                            />
                          )}
                          {task.queue === "Pending_Approval" && (
                            <>
                              <ActionBtn
                                label="Approve"
                                color="bg-green-500 hover:bg-green-600"
                                loading={actionLoading === task.filename}
                                onClick={() =>
                                  handleTaskAction("approve", task)
                                }
                              />
                              <ActionBtn
                                label="Reject"
                                color="bg-red-500 hover:bg-red-600"
                                loading={actionLoading === task.filename}
                                onClick={() =>
                                  handleTaskAction("reject", task)
                                }
                              />
                            </>
                          )}
                          {task.queue === "Approved" && (
                            <ActionBtn
                              label="Execute"
                              color="bg-emerald-600 hover:bg-emerald-700"
                              loading={actionLoading === task.filename}
                              onClick={() =>
                                handleTaskAction("execute", task)
                              }
                            />
                          )}
                          {task.queue === "Rejected" && (
                            <>
                              <ActionBtn
                                label="Reprocess"
                                color="bg-blue-500 hover:bg-blue-600"
                                loading={actionLoading === task.filename}
                                onClick={() =>
                                  handleTaskAction("reprocess", task)
                                }
                              />
                              <ActionBtn
                                label="Delete"
                                color="bg-red-500 hover:bg-red-600"
                                loading={actionLoading === task.filename}
                                onClick={() =>
                                  handleTaskAction("delete", task)
                                }
                              />
                            </>
                          )}
                          {task.queue === "Executing" && (
                            <span className="px-3 py-1.5 bg-yellow-100 text-yellow-800 rounded-lg text-xs font-medium animate-pulse">
                              Executing...
                            </span>
                          )}
                          {task.queue === "Archived" && (
                            <span className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-xs font-medium">
                              Completed
                            </span>
                          )}
                          <button
                            onClick={() => openSlideOver(task.filename)}
                            className="px-3 py-1.5 text-xs font-medium text-rose-gold border border-rose-gold/30 rounded-lg hover:bg-rose-gold/5 transition-colors"
                          >
                            View
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Slide-over */}
              <TaskSlideOver
                open={slideOpen}
                task={selectedTask}
                onClose={() => setSlideOpen(false)}
              />
            </motion.div>
          )}

          {/* ═══════════ ACTIVITY LOG ═══════════ */}
          {tab === "activity" && (
            <motion.div
              key="activity"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {/* Filters */}
              <div className="flex flex-wrap gap-3 mb-6">
                <input
                  type="date"
                  value={auditDate}
                  onChange={(e) => setAuditDate(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                />
                <select
                  value={auditAction}
                  onChange={(e) => setAuditAction(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                >
                  <option value="">All Actions</option>
                  {[
                    "task.created",
                    "task.processed",
                    "task.approved",
                    "task.rejected",
                    "task.reprocessed",
                    "task.deleted",
                  ].map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
                <select
                  value={auditType}
                  onChange={(e) => setAuditType(e.target.value)}
                  className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-rose-gold/30"
                >
                  <option value="">All Types</option>
                  {["order", "inquiry", "alert", "report"].map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <button
                  onClick={loadAudit}
                  className="px-4 py-2 text-sm font-medium bg-rose-gold text-white rounded-xl hover:bg-rose-gold/90 transition-colors"
                >
                  Search
                </button>
              </div>

              {/* Audit table */}
              {auditLoading ? (
                <LoadingSpinner />
              ) : auditEntries.length === 0 ? (
                <EmptyState icon="📜" message="No audit entries found" />
              ) : (
                <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(183,110,121,0.06)] overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-blush/40">
                          {["Timestamp", "Source", "Action", "Entity", "Status", "Actor"].map(
                            (h) => (
                              <th
                                key={h}
                                className="text-left px-5 py-3 text-xs font-semibold text-dark/50 uppercase tracking-wider"
                              >
                                {h}
                              </th>
                            )
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {auditEntries.map((entry, i) => (
                          <motion.tr
                            key={entry.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.03 }}
                            className="border-b border-blush/20 last:border-0 hover:bg-beige/20 transition-colors"
                          >
                            <td className="px-5 py-3 text-xs text-dark/60 whitespace-nowrap">
                              {formatTime(entry.timestamp)}
                            </td>
                            <td className="px-5 py-3 text-xs text-dark/60">
                              {entry.source}
                            </td>
                            <td className="px-5 py-3 text-xs font-medium text-dark">
                              {entry.action}
                            </td>
                            <td className="px-5 py-3 text-xs text-dark/60 max-w-[200px] truncate">
                              {entry.entity_type}: {entry.entity_id}
                            </td>
                            <td className="px-5 py-3">
                              <AIStatusBadge status={entry.status} />
                            </td>
                            <td className="px-5 py-3 text-xs text-dark/50">
                              {entry.actor || "system"}
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* ═══════════ MEMORY ═══════════ */}
          {tab === "memory" && (
            <motion.div
              key="memory"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {/* Sub-tabs */}
              <div className="flex gap-1 mb-6 bg-white rounded-xl p-1 shadow-[0_1px_8px_rgba(183,110,121,0.05)] w-fit">
                {(["clients", "finance", "projects"] as MemoryTab[]).map(
                  (mt) => (
                    <button
                      key={mt}
                      onClick={() => setMemTab(mt)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 capitalize ${
                        memTab === mt
                          ? "bg-rose-gold text-white shadow-[0_4px_12px_rgba(183,110,121,0.3)]"
                          : "text-dark/50 hover:text-dark hover:bg-beige/50"
                      }`}
                    >
                      {mt}
                    </button>
                  )
                )}
              </div>

              {/* Master-detail */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* File list */}
                <div className="lg:col-span-1">
                  <ChartCard
                    title={`${memTab.charAt(0).toUpperCase() + memTab.slice(1)} Files`}
                    subtitle={`${memFiles.length} files`}
                  >
                    {memLoading ? (
                      <LoadingSpinner />
                    ) : memFiles.length === 0 ? (
                      <EmptyState icon="📁" message={`No ${memTab} files`} />
                    ) : (
                      <div className="space-y-1 max-h-[500px] overflow-y-auto">
                        {memFiles.map((file) => (
                          <button
                            key={file.slug}
                            onClick={() => loadMemoryContent(file.slug)}
                            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                              memSelected === file.slug
                                ? "bg-rose-gold/10 text-rose-gold font-medium"
                                : "text-dark/70 hover:bg-beige/50"
                            }`}
                          >
                            <p className="truncate font-medium">{file.slug}</p>
                            <p className="text-xs text-dark/30 mt-0.5">
                              {(file.size / 1024).toFixed(1)} KB ·{" "}
                              {formatTime(file.modified)}
                            </p>
                          </button>
                        ))}
                      </div>
                    )}
                  </ChartCard>
                </div>

                {/* Content viewer */}
                <div className="lg:col-span-2">
                  <ChartCard
                    title={memSelected || "Select a file"}
                    subtitle={memSelected ? "File content" : "Click a file to preview"}
                  >
                    {memContent ? (
                      <pre className="whitespace-pre-wrap text-sm text-dark/80 leading-relaxed max-h-[500px] overflow-y-auto font-[family-name:var(--font-body)]">
                        {memContent}
                      </pre>
                    ) : (
                      <EmptyState icon="📄" message="No file selected" />
                    )}
                  </ChartCard>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// Sub-components
// ════════════════════════════════════════════════════════════════

function StatCard({
  label,
  value,
  subtitle,
  icon,
  trend,
  trendUp,
  gradient,
  iconBg,
}: {
  label: string;
  value: string;
  subtitle: string;
  icon: string;
  trend: string;
  trendUp: boolean;
  gradient: string;
  iconBg: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(183,110,121,0.06)] p-6 relative overflow-hidden group hover:shadow-[0_4px_24px_rgba(183,110,121,0.12)] transition-shadow duration-300"
    >
      <div
        className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
      />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div
            className={`w-11 h-11 ${iconBg} rounded-xl flex items-center justify-center text-xl`}
          >
            {icon}
          </div>
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${
              trendUp
                ? "bg-green-50 text-green-600"
                : "bg-red-50 text-red-500"
            }`}
          >
            {trend}
          </span>
        </div>
        <p className="text-sm text-dark/45 mb-1">{label}</p>
        <p className="text-2xl font-bold text-dark">{value}</p>
        <p className="text-xs text-dark/30 mt-1">{subtitle}</p>
      </div>
    </motion.div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
  className = "",
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-white rounded-2xl shadow-[0_2px_16px_rgba(183,110,121,0.06)] p-6 ${className}`}
    >
      <div className="mb-4">
        <h3 className="font-[family-name:var(--font-heading)] font-bold text-dark text-lg">
          {title}
        </h3>
        <p className="text-xs text-dark/40 mt-0.5">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function MiniStat({
  label,
  value,
  color,
}: {
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-[0_1px_8px_rgba(183,110,121,0.05)] p-4 text-center">
      <p className="text-xs text-dark/40 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function AIStatusBadge({ status }: { status: string }) {
  const s = status?.toUpperCase() || "";
  const styles: Record<string, string> = {
    NEEDS_ACTION: "bg-amber-50 text-amber-700 border-amber-200",
    PENDING_APPROVAL: "bg-blue-50 text-blue-700 border-blue-200",
    APPROVED: "bg-green-50 text-green-700 border-green-200",
    REJECTED: "bg-red-50 text-red-700 border-red-200",
    EXECUTING: "bg-yellow-50 text-yellow-700 border-yellow-200",
    ARCHIVED: "bg-gray-50 text-gray-700 border-gray-200",
    ACTIVE: "bg-green-50 text-green-700 border-green-200",
    COMPLETED: "bg-green-50 text-green-700 border-green-200",
    ERROR: "bg-red-50 text-red-700 border-red-200",
    PENDING: "bg-yellow-50 text-yellow-700 border-yellow-200",
    PLANS: "bg-purple-50 text-purple-700 border-purple-200",
  };
  return (
    <span
      className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase border ${
        styles[s] || "bg-gray-50 text-gray-700 border-gray-200"
      }`}
    >
      {status?.replace(/_/g, " ") || "Unknown"}
    </span>
  );
}

function QueuePipeline({
  needsAction,
  pendingApproval,
  approved,
  rejected,
}: {
  needsAction: number;
  pendingApproval: number;
  approved: number;
  rejected: number;
}) {
  const stages = [
    { label: "Needs Action", count: needsAction, color: "bg-amber-500", lightBg: "bg-amber-50" },
    { label: "Pending Approval", count: pendingApproval, color: "bg-blue-500", lightBg: "bg-blue-50" },
    { label: "Approved", count: approved, color: "bg-green-500", lightBg: "bg-green-50" },
    { label: "Rejected", count: rejected, color: "bg-red-500", lightBg: "bg-red-50" },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(183,110,121,0.06)] p-6 mb-8">
      <h3 className="font-[family-name:var(--font-heading)] font-bold text-dark text-lg mb-1">
        Queue Pipeline
      </h3>
      <p className="text-xs text-dark/40 mb-5">Task flow through processing stages</p>
      <div className="flex items-center justify-between gap-2 overflow-x-auto">
        {stages.map((stage, i) => (
          <div key={stage.label} className="flex items-center gap-2 min-w-0">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`${stage.lightBg} rounded-xl px-4 py-3 text-center min-w-[120px]`}
            >
              <p className={`text-2xl font-bold`} style={{ color: BRAND.dark }}>
                {stage.count}
              </p>
              <p className="text-xs text-dark/50 mt-0.5 whitespace-nowrap">{stage.label}</p>
              <div className={`h-1 ${stage.color} rounded-full mt-2 opacity-60`} />
            </motion.div>
            {i < stages.length - 1 && (
              <svg
                className="w-5 h-5 text-dark/20 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function TaskSlideOver({
  open,
  task,
  onClose,
}: {
  open: boolean;
  task: TaskDetail | null;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open && task && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-40"
          />
          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-white shadow-2xl z-50 overflow-y-auto"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-[family-name:var(--font-heading)] font-bold text-dark text-lg truncate pr-4">
                  {task.filename}
                </h2>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg bg-beige flex items-center justify-center text-dark/50 hover:text-dark transition-colors shrink-0"
                >
                  ✕
                </button>
              </div>

              {/* Metadata */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <AIStatusBadge status={task.queue} />
                </div>
                {Object.keys(task.metadata).length > 0 && (
                  <table className="w-full text-sm">
                    <tbody>
                      {Object.entries(task.metadata).map(([key, val]) => (
                        <tr
                          key={key}
                          className="border-b border-blush/20 last:border-0"
                        >
                          <td className="py-2 pr-4 text-dark/50 font-medium">
                            {key}
                          </td>
                          <td className="py-2 text-dark">{val}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Content */}
              <div className="border-t border-blush/30 pt-4">
                <h3 className="text-sm font-semibold text-dark/60 mb-3">
                  Content
                </h3>
                <pre className="whitespace-pre-wrap text-sm text-dark/80 leading-relaxed bg-beige/30 rounded-xl p-4 max-h-[60vh] overflow-y-auto">
                  {task.content}
                </pre>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function EmptyState({ icon, message }: { icon: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-dark/30">
      <div className="text-4xl mb-3">{icon}</div>
      <p className="text-sm">{message}</p>
    </div>
  );
}

function ActionBtn({
  label,
  color,
  loading,
  onClick,
}: {
  label: string;
  color: string;
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`px-3 py-1.5 text-xs font-medium text-white rounded-lg transition-colors disabled:opacity-50 ${color}`}
    >
      {loading ? "..." : label}
    </button>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div
        className="w-8 h-8 border-3 border-rose-gold/30 border-t-rose-gold rounded-full animate-spin"
      />
    </div>
  );
}

// ── Helpers ──

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function actionIcon(action: string): string {
  if (action.includes("approved")) return "✅";
  if (action.includes("rejected")) return "❌";
  if (action.includes("created")) return "📝";
  if (action.includes("processed")) return "⚙️";
  if (action.includes("deleted")) return "🗑️";
  if (action.includes("reprocessed")) return "🔄";
  return "📋";
}
