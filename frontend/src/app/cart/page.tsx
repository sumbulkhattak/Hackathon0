"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { useCart } from "@/components/CartProvider";

export default function CartPage() {
  const { items, removeFromCart, updateQuantity, totalPrice } = useCart();

  if (items.length === 0) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="text-6xl mb-6">🛒</div>
          <h2 className="text-2xl font-bold text-dark mb-4">Your cart is empty</h2>
          <p className="text-dark/50 mb-8">
            Looks like you haven&apos;t added any sparkle yet!
          </p>
          <Link
            href="/shop"
            className="bg-rose-gold text-white px-8 py-3.5 rounded-full font-medium hover:bg-rose-gold-dark transition-all duration-300 shadow-[0_4px_20px_rgba(183,110,121,0.1)]"
          >
            Start Shopping
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl lg:text-4xl font-bold text-dark mb-8"
        >
          Shopping Cart
        </motion.h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item, index) => (
              <motion.div
                key={item.product.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex gap-4 p-4 bg-white rounded-2xl shadow-[0_4px_20px_rgba(183,110,121,0.1)] border border-blush/30"
              >
                <div className="relative w-24 h-24 rounded-xl overflow-hidden bg-beige flex-shrink-0">
                  <Image
                    src={item.product.image_url}
                    alt={item.product.name}
                    fill
                    className="object-cover"
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <Link
                    href={`/product/${item.product.slug}`}
                    className="font-[family-name:var(--font-heading)] font-semibold text-dark hover:text-rose-gold transition-colors line-clamp-1"
                  >
                    {item.product.name}
                  </Link>
                  <p className="text-sm text-dark/40 mt-1">{item.product.category_name}</p>
                  <p className="text-rose-gold-dark font-bold mt-1">
                    ₹{item.product.price.toLocaleString("en-IN")}
                  </p>
                </div>

                <div className="flex flex-col items-end justify-between">
                  <button
                    onClick={() => removeFromCart(item.product.id)}
                    className="text-dark/30 hover:text-red-500 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>

                  <div className="flex items-center border border-blush rounded-full overflow-hidden">
                    <button
                      onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                      className="px-3 py-1 text-sm text-dark hover:bg-blush transition-colors"
                    >
                      -
                    </button>
                    <span className="px-3 py-1 text-sm font-medium">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                      className="px-3 py-1 text-sm text-dark hover:bg-blush transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Order Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-blush to-cream p-6 rounded-2xl h-fit sticky top-24"
          >
            <h3 className="font-[family-name:var(--font-heading)] text-xl font-bold text-dark mb-6">
              Order Summary
            </h3>

            <div className="space-y-3 text-sm">
              {items.map((item) => (
                <div key={item.product.id} className="flex justify-between text-dark/60">
                  <span className="truncate mr-2">
                    {item.product.name} x{item.quantity}
                  </span>
                  <span className="font-medium text-dark">
                    ₹{(item.product.price * item.quantity).toLocaleString("en-IN")}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t border-rose-gold/20 mt-4 pt-4">
              <div className="flex justify-between text-dark/60 text-sm mb-2">
                <span>Shipping</span>
                <span className="text-green-600 font-medium">Free</span>
              </div>
              <div className="flex justify-between text-dark font-bold text-lg mt-2">
                <span>Total</span>
                <span className="text-rose-gold-dark">₹{totalPrice.toLocaleString("en-IN")}</span>
              </div>
            </div>

            <Link
              href="/checkout"
              className="block text-center bg-rose-gold text-white px-8 py-3.5 rounded-full font-medium hover:bg-rose-gold-dark transition-all duration-300 shadow-[0_4px_20px_rgba(183,110,121,0.1)] hover:shadow-[0_8px_30px_rgba(183,110,121,0.2)] mt-6"
            >
              Proceed to Checkout
            </Link>

            <Link
              href="/shop"
              className="block text-center text-rose-gold text-sm mt-3 hover:underline"
            >
              Continue Shopping
            </Link>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
