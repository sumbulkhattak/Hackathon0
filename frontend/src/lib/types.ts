export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: number;
  image_url: string;
  images: string[];
  category_id: number;
  category_name: string;
  stock: number;
  featured: boolean;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface OrderItemCreate {
  product_id: number;
  quantity: number;
}

export interface OrderCreate {
  customer_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  items: OrderItemCreate[];
}

export interface OrderItemResponse {
  id: number;
  product_id: number;
  quantity: number;
  price: number;
}

export interface Order {
  id: number;
  customer_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  total: number;
  status: string;
  created_at: string;
  items: OrderItemResponse[];
}

export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  total_products: number;
  low_stock_count: number;
}
