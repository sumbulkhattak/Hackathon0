"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import {
  getStats,
  getOrders,
  getProducts,
  updateOrderStatus,
  deleteProduct,
} from "@/lib/api";
import { DashboardStats, Order, Product } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from "recharts";

type Tab = "overview" | "orders" | "products" | "analytics";

// ─── Brand colors ─────────────────────────────────────────────────────────────
const BRAND = {
  rose: "#C9A84C",
  roseDark: "#A07B28",
  roseLight: "#E8D48B",
  blush: "#1A1A1A",
  beige: "#151515",
  cream: "#111111",
  dark: "#1A1410",
};

const PIE_COLORS = ["#C9A84C", "#E8D48B", "#A07B28", "#D4BF7A", "#8B6914", "#F0E0A0"];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, o, p] = await Promise.all([
        getStats(),
        getOrders(),
        getProducts(),
      ]);
      setStats(s);
      setOrders(o);
      setProducts(p);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (orderId: number, status: string) => {
    try {
      await updateOrderStatus(orderId, status);
      setOrders((prev) =>
        prev.map((o) => (o.id === orderId ? { ...o, status } : o))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm("Are you sure you want to delete this product?")) return;
    try {
      await deleteProduct(productId);
      setProducts((prev) => prev.filter((p) => p.id !== productId));
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  // ─── Derived analytics data ─────────────────────────────────────────────────
  const categoryData = useMemo(() => {
    const map: Record<string, { count: number; revenue: number; stock: number }> = {};
    products.forEach((p) => {
      const cat = p.category_name || "Other";
      if (!map[cat]) map[cat] = { count: 0, revenue: 0, stock: 0 };
      map[cat].count += 1;
      map[cat].stock += p.stock;
    });
    // Add revenue from orders
    orders.forEach((o) => {
      o.items.forEach((item) => {
        const prod = products.find((p) => p.id === item.product_id);
        const cat = prod?.category_name || "Other";
        if (!map[cat]) map[cat] = { count: 0, revenue: 0, stock: 0 };
        map[cat].revenue += item.price * item.quantity;
      });
    });
    return Object.entries(map).map(([name, data]) => ({ name, ...data }));
  }, [products, orders]);

  const stockData = useMemo(() => {
    return products
      .map((p) => ({
        name: p.name.length > 18 ? p.name.substring(0, 18) + "…" : p.name,
        fullName: p.name,
        stock: p.stock,
        fill:
          p.stock <= 3
            ? "#EF4444"
            : p.stock <= 10
            ? "#F59E0B"
            : BRAND.rose,
      }))
      .sort((a, b) => a.stock - b.stock);
  }, [products]);

  const orderStatusData = useMemo(() => {
    const map: Record<string, number> = {};
    orders.forEach((o) => {
      map[o.status] = (map[o.status] || 0) + 1;
    });
    return Object.entries(map).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
    }));
  }, [orders]);

  const revenueByDay = useMemo(() => {
    const map: Record<string, number> = {};
    orders.forEach((o) => {
      const day = new Date(o.created_at).toLocaleDateString("en-IN", {
        month: "short",
        day: "numeric",
      });
      map[day] = (map[day] || 0) + o.total;
    });
    return Object.entries(map).map(([date, revenue]) => ({ date, revenue }));
  }, [orders]);

  const topProducts = useMemo(() => {
    const map: Record<number, { name: string; quantity: number; revenue: number }> = {};
    orders.forEach((o) => {
      o.items.forEach((item) => {
        const prod = products.find((p) => p.id === item.product_id);
        if (!map[item.product_id]) {
          map[item.product_id] = {
            name: prod?.name || `Product #${item.product_id}`,
            quantity: 0,
            revenue: 0,
          };
        }
        map[item.product_id].quantity += item.quantity;
        map[item.product_id].revenue += item.price * item.quantity;
      });
    });
    return Object.values(map)
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 5);
  }, [orders, products]);

  const priceDistribution = useMemo(() => {
    const ranges = [
      { range: "Rs.0-399", min: 0, max: 399, count: 0 },
      { range: "Rs.400-699", min: 400, max: 699, count: 0 },
      { range: "Rs.700-999", min: 700, max: 999, count: 0 },
      { range: "Rs.1000+", min: 1000, max: Infinity, count: 0 },
    ];
    products.forEach((p) => {
      const r = ranges.find((r) => p.price >= r.min && p.price <= r.max);
      if (r) r.count += 1;
    });
    return ranges.map((r) => ({ name: r.range, products: r.count }));
  }, [products]);

  // ─── Tab config ─────────────────────────────────────────────────────────────
  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: "overview", label: "Overview", icon: "📊" },
    { key: "analytics", label: "Analytics", icon: "📈" },
    { key: "orders", label: "Orders", icon: "📦" },
    { key: "products", label: "Products", icon: "💎" },
  ];

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[60vh] gap-4">
        <div className="w-12 h-12 border-3 border-rose-gold border-t-transparent rounded-full animate-spin" />
        <p className="text-dark/40 text-sm">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="bg-beige/30 min-h-screen pt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-dark mb-1">
              Dashboard
            </h1>
            <p className="text-dark/40 text-sm">
              Welcome back to Royal Sparkle Admin
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-rose-gold to-rose-gold-dark flex items-center justify-center text-white text-sm font-bold">
              RS
            </div>
            <div>
              <p className="text-sm font-medium text-dark">Admin</p>
              <p className="text-xs text-dark/40">Royal Sparkle</p>
            </div>
          </div>
        </motion.div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-8 bg-white rounded-2xl p-1.5 shadow-[0_2px_12px_rgba(201,168,76,0.08)] w-fit">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
                tab === t.key
                  ? "bg-rose-gold text-white shadow-[0_4px_12px_rgba(201,168,76,0.3)]"
                  : "text-dark/50 hover:text-dark hover:bg-beige/50"
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* ═══ OVERVIEW TAB ════════════════════════════════════════════════ */}
          {tab === "overview" && stats && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              {/* Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <StatCard
                  label="Total Revenue"
                  value={`Rs.${stats.total_revenue.toLocaleString("en-IN")}`}
                  subtitle="All time"
                  icon="💰"
                  trend="+12.5%"
                  trendUp={true}
                  gradient="from-rose-gold/10 to-blush/40"
                  iconBg="bg-rose-gold/15"
                />
                <StatCard
                  label="Total Orders"
                  value={stats.total_orders.toString()}
                  subtitle="Lifetime orders"
                  icon="📦"
                  trend="+8.2%"
                  trendUp={true}
                  gradient="from-blush/30 to-cream"
                  iconBg="bg-blush"
                />
                <StatCard
                  label="Products"
                  value={stats.total_products.toString()}
                  subtitle="Active listings"
                  icon="💎"
                  trend="Stable"
                  trendUp={true}
                  gradient="from-cream to-beige"
                  iconBg="bg-cream"
                />
                <StatCard
                  label="Low Stock"
                  value={stats.low_stock_count.toString()}
                  subtitle="Need restock"
                  icon="⚠️"
                  trend={stats.low_stock_count > 0 ? "Action needed" : "All good"}
                  trendUp={stats.low_stock_count === 0}
                  gradient="from-beige to-blush/20"
                  iconBg="bg-beige"
                />
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Revenue Chart */}
                <ChartCard title="Revenue Trend" subtitle="Daily revenue" className="lg:col-span-2">
                  {revenueByDay.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <AreaChart data={revenueByDay}>
                        <defs>
                          <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={BRAND.rose} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={BRAND.rose} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12, fill: "#1A141080" }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fontSize: 12, fill: "#1A141080" }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={(v) => `Rs.${v.toLocaleString()}`}
                        />
                        <Tooltip
                          formatter={(value) => [`Rs.${Number(value).toLocaleString("en-IN")}`, "Revenue"]}
                          contentStyle={{
                            borderRadius: "12px",
                            border: "none",
                            boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                            fontSize: "13px",
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="revenue"
                          stroke={BRAND.rose}
                          strokeWidth={2.5}
                          fill="url(#revenueGrad)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No revenue data yet. Place orders to see trends." />
                  )}
                </ChartCard>

                {/* Order Status Pie */}
                <ChartCard title="Order Status" subtitle="Distribution">
                  {orderStatusData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie
                          data={orderStatusData}
                          cx="50%"
                          cy="45%"
                          innerRadius={55}
                          outerRadius={90}
                          paddingAngle={4}
                          dataKey="value"
                        >
                          {orderStatusData.map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={PIE_COLORS[index % PIE_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            borderRadius: "12px",
                            border: "none",
                            boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                            fontSize: "13px",
                          }}
                        />
                        <Legend
                          verticalAlign="bottom"
                          iconType="circle"
                          iconSize={8}
                          wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No orders yet" />
                  )}
                </ChartCard>
              </div>

              {/* Recent Orders + Top Products Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Orders */}
                <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-6">
                  <div className="flex justify-between items-center mb-5">
                    <div>
                      <h3 className="font-[family-name:var(--font-heading)] font-bold text-dark text-lg">
                        Recent Orders
                      </h3>
                      <p className="text-xs text-dark/40 mt-0.5">Latest transactions</p>
                    </div>
                    <button
                      onClick={() => setTab("orders")}
                      className="text-xs text-rose-gold hover:text-rose-gold-dark font-medium transition-colors"
                    >
                      View All →
                    </button>
                  </div>
                  {orders.length === 0 ? (
                    <p className="text-dark/30 text-sm text-center py-8">No orders yet</p>
                  ) : (
                    <div className="space-y-3">
                      {orders.slice(0, 5).map((order, i) => (
                        <motion.div
                          key={order.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-center justify-between p-3 rounded-xl hover:bg-beige/30 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blush to-cream flex items-center justify-center text-sm font-bold text-rose-gold-dark">
                              #{order.id}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-dark">
                                {order.customer_name}
                              </p>
                              <p className="text-xs text-dark/40">
                                {order.items.length} item(s) •{" "}
                                {new Date(order.created_at).toLocaleDateString("en-IN", {
                                  day: "numeric",
                                  month: "short",
                                })}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold text-dark">
                              Rs.{order.total.toLocaleString("en-IN")}
                            </p>
                            <StatusBadge status={order.status} />
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Top Products */}
                <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-6">
                  <div className="flex justify-between items-center mb-5">
                    <div>
                      <h3 className="font-[family-name:var(--font-heading)] font-bold text-dark text-lg">
                        Top Products
                      </h3>
                      <p className="text-xs text-dark/40 mt-0.5">Best sellers by revenue</p>
                    </div>
                    <button
                      onClick={() => setTab("products")}
                      className="text-xs text-rose-gold hover:text-rose-gold-dark font-medium transition-colors"
                    >
                      View All →
                    </button>
                  </div>
                  {topProducts.length === 0 ? (
                    <p className="text-dark/30 text-sm text-center py-8">
                      No sales data yet
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {topProducts.map((item, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="flex items-center justify-between p-3 rounded-xl hover:bg-beige/30 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-gold/10 to-blush flex items-center justify-center text-sm font-bold text-rose-gold-dark">
                              {i + 1}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-dark">{item.name}</p>
                              <p className="text-xs text-dark/40">
                                {item.quantity} units sold
                              </p>
                            </div>
                          </div>
                          <p className="text-sm font-semibold text-rose-gold-dark">
                            Rs.{item.revenue.toLocaleString("en-IN")}
                          </p>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* ═══ ANALYTICS TAB ═══════════════════════════════════════════════ */}
          {tab === "analytics" && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* Category Breakdown + Price Distribution */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard title="Revenue by Category" subtitle="Sales distribution across categories">
                  {categoryData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={categoryData}
                          cx="50%"
                          cy="45%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={3}
                          dataKey="revenue"
                          nameKey="name"
                        >
                          {categoryData.map((_, index) => (
                            <Cell
                              key={`cat-${index}`}
                              fill={PIE_COLORS[index % PIE_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value) => [`Rs.${Number(value).toLocaleString("en-IN")}`, "Revenue"]}
                          contentStyle={{
                            borderRadius: "12px",
                            border: "none",
                            boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                            fontSize: "13px",
                          }}
                        />
                        <Legend
                          verticalAlign="bottom"
                          iconType="circle"
                          iconSize={8}
                          wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No category data" />
                  )}
                </ChartCard>

                <ChartCard title="Price Distribution" subtitle="Product count by price range">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={priceDistribution} barSize={40}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 12, fill: "#1A141080" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: "#1A141080" }}
                        axisLine={false}
                        tickLine={false}
                        allowDecimals={false}
                      />
                      <Tooltip
                        contentStyle={{
                          borderRadius: "12px",
                          border: "none",
                          boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                          fontSize: "13px",
                        }}
                      />
                      <Bar dataKey="products" fill={BRAND.rose} radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>

              {/* Inventory Levels */}
              <ChartCard title="Inventory Levels" subtitle="Current stock per product">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={stockData} layout="vertical" barSize={16} margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" horizontal={false} />
                    <XAxis
                      type="number"
                      tick={{ fontSize: 12, fill: "#1A141080" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={{ fontSize: 11, fill: "#1A141080" }}
                      axisLine={false}
                      tickLine={false}
                      width={140}
                    />
                    <Tooltip
                      formatter={(value, _name, props) => [
                        `${value} units`,
                        (props as { payload: { fullName: string } }).payload.fullName,
                      ]}
                      contentStyle={{
                        borderRadius: "12px",
                        border: "none",
                        boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                        fontSize: "13px",
                      }}
                    />
                    <Bar dataKey="stock" radius={[0, 6, 6, 0]}>
                      {stockData.map((entry, index) => (
                        <Cell key={`stock-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              {/* Products per Category */}
              <ChartCard title="Products per Category" subtitle="Category distribution">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={categoryData} barSize={45}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12, fill: "#1A141080" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: "#1A141080" }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "12px",
                        border: "none",
                        boxShadow: "0 4px 20px rgba(201,168,76,0.15)",
                        fontSize: "13px",
                      }}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: "12px" }}
                    />
                    <Bar
                      dataKey="count"
                      name="Products"
                      fill={BRAND.rose}
                      radius={[8, 8, 0, 0]}
                    />
                    <Bar
                      dataKey="stock"
                      name="Total Stock"
                      fill={BRAND.roseLight}
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </motion.div>
          )}

          {/* ═══ ORDERS TAB ══════════════════════════════════════════════════ */}
          {tab === "orders" && (
            <motion.div
              key="orders"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {/* Summary mini-cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <MiniStat
                  label="All Orders"
                  value={orders.length}
                  color="text-dark"
                />
                <MiniStat
                  label="Pending"
                  value={orders.filter((o) => o.status === "pending").length}
                  color="text-yellow-600"
                />
                <MiniStat
                  label="Confirmed"
                  value={orders.filter((o) => o.status === "confirmed").length}
                  color="text-blue-600"
                />
                <MiniStat
                  label="Delivered"
                  value={orders.filter((o) => o.status === "delivered").length}
                  color="text-green-600"
                />
              </div>

              {orders.length === 0 ? (
                <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-12 text-center">
                  <div className="text-5xl mb-4">📦</div>
                  <p className="text-dark/40">No orders yet. Orders will appear here once customers start shopping.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {orders.map((order, i) => (
                    <motion.div
                      key={order.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-6 hover:shadow-[0_4px_24px_rgba(201,168,76,0.12)] transition-shadow duration-300"
                    >
                      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                        <div className="flex gap-4">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blush to-cream flex items-center justify-center text-lg font-bold text-rose-gold-dark shrink-0">
                            #{order.id}
                          </div>
                          <div>
                            <div className="flex items-center gap-3 mb-1.5">
                              <h3 className="font-[family-name:var(--font-heading)] font-bold text-dark">
                                {order.customer_name}
                              </h3>
                              <StatusBadge status={order.status} />
                            </div>
                            <p className="text-sm text-dark/50">
                              {order.email} • {order.phone}
                            </p>
                            <p className="text-sm text-dark/35 mt-0.5">
                              {order.address}, {order.city}
                            </p>
                            <div className="flex items-center gap-3 mt-2 text-xs text-dark/40">
                              <span>{order.items.length} item(s)</span>
                              <span>•</span>
                              <span>
                                {new Date(order.created_at).toLocaleDateString("en-IN", {
                                  day: "numeric",
                                  month: "long",
                                  year: "numeric",
                                })}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 sm:ml-auto">
                          <span className="text-xl font-bold text-rose-gold-dark whitespace-nowrap">
                            Rs.{order.total.toLocaleString("en-IN")}
                          </span>
                          <select
                            value={order.status}
                            onChange={(e) =>
                              handleStatusChange(order.id, e.target.value)
                            }
                            className="border border-blush rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:border-rose-gold focus:ring-1 focus:ring-rose-gold/20 transition-all"
                          >
                            <option value="pending">Pending</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="shipped">Shipped</option>
                            <option value="delivered">Delivered</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* ═══ PRODUCTS TAB ════════════════════════════════════════════════ */}
          {tab === "products" && (
            <motion.div
              key="products"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {/* Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <MiniStat
                  label="All Products"
                  value={products.length}
                  color="text-dark"
                />
                <MiniStat
                  label="Featured"
                  value={products.filter((p) => p.featured).length}
                  color="text-rose-gold-dark"
                />
                <MiniStat
                  label="Low Stock"
                  value={products.filter((p) => p.stock < 10).length}
                  color="text-orange-500"
                />
                <MiniStat
                  label="Total Value"
                  value={`Rs.${products
                    .reduce((sum, p) => sum + p.price * p.stock, 0)
                    .toLocaleString("en-IN")}`}
                  color="text-green-600"
                  isText
                />
              </div>

              <div className="bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-blush/50">
                        <th className="text-left py-4 px-6 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="text-left py-4 px-4 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="text-left py-4 px-4 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="text-left py-4 px-4 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Stock
                        </th>
                        <th className="text-left py-4 px-4 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="text-right py-4 px-6 text-xs font-semibold text-dark/40 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {products.map((product, i) => (
                        <motion.tr
                          key={product.id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: i * 0.03 }}
                          className="border-b border-blush/20 hover:bg-beige/20 transition-colors"
                        >
                          <td className="py-4 px-6">
                            <div className="flex items-center gap-3">
                              <div className="relative w-10 h-10 rounded-xl overflow-hidden bg-beige shrink-0">
                                <Image
                                  src={product.image_url}
                                  alt={product.name}
                                  fill
                                  className="object-cover"
                                />
                              </div>
                              <div>
                                <p className="font-medium text-dark text-sm">
                                  {product.name}
                                </p>
                                {product.featured && (
                                  <span className="text-[10px] bg-rose-gold/10 text-rose-gold-dark px-2 py-0.5 rounded-full font-medium">
                                    Featured
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            <span className="text-sm text-dark/50 bg-beige/50 px-2.5 py-1 rounded-lg">
                              {product.category_name}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-sm font-semibold text-dark">
                            Rs.{product.price.toLocaleString("en-IN")}
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  product.stock <= 3
                                    ? "bg-red-500"
                                    : product.stock <= 10
                                    ? "bg-yellow-500"
                                    : "bg-green-500"
                                }`}
                              />
                              <span
                                className={`text-sm font-medium ${
                                  product.stock <= 3
                                    ? "text-red-600"
                                    : product.stock <= 10
                                    ? "text-yellow-600"
                                    : "text-green-600"
                                }`}
                              >
                                {product.stock}
                              </span>
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            {product.stock === 0 ? (
                              <span className="text-xs bg-red-50 text-red-600 px-2.5 py-1 rounded-full font-medium">
                                Out of Stock
                              </span>
                            ) : product.stock <= 10 ? (
                              <span className="text-xs bg-yellow-50 text-yellow-700 px-2.5 py-1 rounded-full font-medium">
                                Low Stock
                              </span>
                            ) : (
                              <span className="text-xs bg-green-50 text-green-700 px-2.5 py-1 rounded-full font-medium">
                                In Stock
                              </span>
                            )}
                          </td>
                          <td className="py-4 px-6 text-right">
                            <button
                              onClick={() => handleDeleteProduct(product.id)}
                              className="text-red-400 hover:text-red-600 text-xs font-medium transition-colors hover:bg-red-50 px-3 py-1.5 rounded-lg"
                            >
                              Delete
                            </button>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────────────────

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
      className={`bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-6 relative overflow-hidden group hover:shadow-[0_4px_24px_rgba(201,168,76,0.12)] transition-shadow duration-300`}
    >
      {/* Background gradient accent */}
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
      className={`bg-white rounded-2xl shadow-[0_2px_16px_rgba(201,168,76,0.06)] p-6 ${className}`}
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

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[280px] text-dark/30">
      <div className="text-4xl mb-3">📊</div>
      <p className="text-sm">{message}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-yellow-50 text-yellow-700 border-yellow-200",
    confirmed: "bg-blue-50 text-blue-700 border-blue-200",
    shipped: "bg-purple-50 text-purple-700 border-purple-200",
    delivered: "bg-green-50 text-green-700 border-green-200",
    cancelled: "bg-red-50 text-red-700 border-red-200",
  };

  return (
    <span
      className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold capitalize border ${
        styles[status] || "bg-gray-50 text-gray-700 border-gray-200"
      }`}
    >
      {status}
    </span>
  );
}

function MiniStat({
  label,
  value,
  color,
  isText = false,
}: {
  label: string;
  value: number | string;
  color: string;
  isText?: boolean;
}) {
  return (
    <div className="bg-white rounded-xl shadow-[0_1px_8px_rgba(201,168,76,0.05)] p-4 text-center">
      <p className="text-xs text-dark/40 mb-1">{label}</p>
      <p className={`${isText ? "text-lg" : "text-2xl"} font-bold ${color}`}>
        {value}
      </p>
    </div>
  );
}
