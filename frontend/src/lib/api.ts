import { OrderCreate, Product } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(endpoint: string, options?: RequestInit) {
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

export async function getProducts(category?: string, featured?: boolean): Promise<Product[]> {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  if (featured) params.append("featured", "true");
  const query = params.toString();
  return fetchAPI(`/api/products${query ? `?${query}` : ""}`);
}

export async function getProduct(slug: string): Promise<Product> {
  return fetchAPI(`/api/products/${slug}`);
}

export async function getCategories() {
  return fetchAPI("/api/categories");
}

export async function createOrder(order: OrderCreate) {
  return fetchAPI("/api/orders", {
    method: "POST",
    body: JSON.stringify(order),
  });
}

export async function getOrders() {
  return fetchAPI("/api/orders");
}

export async function getOrder(id: number) {
  return fetchAPI(`/api/orders/${id}`);
}

export async function updateOrderStatus(id: number, status: string) {
  return fetchAPI(`/api/orders/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function getStats() {
  return fetchAPI("/api/stats");
}

export async function createProduct(product: Partial<Product>) {
  return fetchAPI("/api/products", {
    method: "POST",
    body: JSON.stringify(product),
  });
}

export async function updateProduct(id: number, product: Partial<Product>) {
  return fetchAPI(`/api/products/${id}`, {
    method: "PUT",
    body: JSON.stringify(product),
  });
}

export async function deleteProduct(id: number) {
  return fetchAPI(`/api/products/${id}`, {
    method: "DELETE",
  });
}
