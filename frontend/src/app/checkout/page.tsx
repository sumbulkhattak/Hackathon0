"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useCart } from "@/components/CartProvider";
import { createOrder } from "@/lib/api";
import Link from "next/link";

export default function CheckoutPage() {
  const router = useRouter();
  const { items, totalPrice, clearCart } = useCart();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [orderId, setOrderId] = useState<number | null>(null);

  const [form, setForm] = useState({
    customer_name: "",
    email: "",
    phone: "",
    address: "",
    city: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const order = await createOrder({
        ...form,
        items: items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
      });
      setOrderId(order.id);
      setSuccess(true);
      clearCart();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0 && !success) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
        <h2 className="text-2xl font-bold text-white mb-4">Nothing to checkout</h2>
        <Link href="/shop" className="text-gold hover:underline">
          Go to Shop
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-surface p-10 rounded-3xl shadow-[0_8px_30px_rgba(201,168,76,0.2)] max-w-md"
        >
          <div className="text-6xl mb-6">🎉</div>
          <h2 className="text-3xl font-bold text-white mb-3">Order Placed!</h2>
          <p className="text-white/60 mb-2">
            Your order <span className="font-bold text-gold">#{orderId}</span> has been
            placed successfully.
          </p>
          <p className="text-white/40 text-sm mb-8">
            We&apos;ll send a confirmation to your email shortly.
          </p>
          <Link
            href="/shop"
            className="bg-gold text-dark px-8 py-3 rounded-full font-medium hover:bg-gold-light transition-all duration-300 inline-block"
          >
            Continue Shopping
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="bg-dark min-h-screen pt-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl lg:text-4xl font-bold text-white mb-8"
        >
          Checkout
        </motion.h1>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Form */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onSubmit={handleSubmit}
            className="lg:col-span-3 space-y-5"
          >
            <h3 className="font-[family-name:var(--font-heading)] text-xl font-bold text-white mb-2">
              Shipping Details
            </h3>

            {error && (
              <div className="bg-red-50 text-red-600 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">Full Name</label>
              <input
                type="text"
                name="customer_name"
                required
                value={form.customer_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gold/20 rounded-xl focus:outline-none focus:border-gold transition-colors bg-surface text-white"
                placeholder="Enter your full name"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/70 mb-1.5">Email</label>
                <input
                  type="email"
                  name="email"
                  required
                  value={form.email}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gold/20 rounded-xl focus:outline-none focus:border-gold transition-colors bg-surface text-white"
                  placeholder="your@email.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-1.5">Phone</label>
                <input
                  type="tel"
                  name="phone"
                  required
                  value={form.phone}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gold/20 rounded-xl focus:outline-none focus:border-gold transition-colors bg-surface text-white"
                  placeholder="+92 300 1234567"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">Address</label>
              <textarea
                name="address"
                required
                value={form.address}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-3 border border-gold/20 rounded-xl focus:outline-none focus:border-gold transition-colors bg-surface text-white resize-none"
                placeholder="Enter your shipping address"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white/70 mb-1.5">City</label>
              <input
                type="text"
                name="city"
                required
                value={form.city}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gold/20 rounded-xl focus:outline-none focus:border-gold transition-colors bg-surface text-white"
                placeholder="Enter your city"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gold text-dark py-4 rounded-full font-medium text-lg hover:bg-gold-light transition-all duration-300 shadow-[0_4px_20px_rgba(201,168,76,0.1)] hover:shadow-[0_8px_30px_rgba(201,168,76,0.2)] disabled:opacity-50 disabled:cursor-not-allowed mt-4"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-5 h-5 border-2 border-dark border-t-transparent rounded-full animate-spin" />
                  Placing Order...
                </span>
              ) : (
                `Place Order — Rs.${totalPrice.toLocaleString("en-IN")}`
              )}
            </button>
          </motion.form>

          {/* Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="bg-surface p-6 rounded-2xl sticky top-24">
              <h3 className="font-[family-name:var(--font-heading)] text-lg font-bold text-white mb-4">
                Order Summary
              </h3>
              <div className="space-y-3 text-sm">
                {items.map((item) => (
                  <div key={item.product.id} className="flex justify-between text-white/60">
                    <span className="truncate mr-2">
                      {item.product.name} x{item.quantity}
                    </span>
                    <span className="font-medium text-white whitespace-nowrap">
                      Rs.{(item.product.price * item.quantity).toLocaleString("en-IN")}
                    </span>
                  </div>
                ))}
              </div>
              <div className="border-t border-gold/20 mt-4 pt-4">
                <div className="flex justify-between text-white/60 text-sm mb-1">
                  <span>Shipping</span>
                  <span className="text-green-600 font-medium">Free</span>
                </div>
                <div className="flex justify-between text-white font-bold text-lg mt-2">
                  <span>Total</span>
                  <span className="text-gold">Rs.{totalPrice.toLocaleString("en-IN")}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
