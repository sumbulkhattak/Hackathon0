"use client";

import Link from "next/link";
import { useCart } from "./CartProvider";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Navbar() {
  const { totalItems } = useCart();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="bg-white/90 backdrop-blur-md sticky top-0 z-50 border-b border-blush">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl">✦</span>
            <span className="font-[family-name:var(--font-heading)] text-xl font-bold text-rose-gold">
              Royal Sparkle
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="text-dark hover:text-rose-gold transition-colors duration-300 font-medium"
            >
              Home
            </Link>
            <Link
              href="/shop"
              className="text-dark hover:text-rose-gold transition-colors duration-300 font-medium"
            >
              Shop
            </Link>
            <Link
              href="/admin"
              className="text-dark hover:text-rose-gold transition-colors duration-300 font-medium"
            >
              Admin
            </Link>
            <Link
              href="/cart"
              className="relative text-dark hover:text-rose-gold transition-colors duration-300"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
                />
              </svg>
              {totalItems > 0 && (
                <span className="absolute -top-2 -right-2 bg-rose-gold text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                  {totalItems}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-dark"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden bg-white border-t border-blush overflow-hidden"
          >
            <div className="px-4 py-3 space-y-3">
              <Link href="/" onClick={() => setMobileOpen(false)} className="block text-dark hover:text-rose-gold font-medium">Home</Link>
              <Link href="/shop" onClick={() => setMobileOpen(false)} className="block text-dark hover:text-rose-gold font-medium">Shop</Link>
              <Link href="/admin" onClick={() => setMobileOpen(false)} className="block text-dark hover:text-rose-gold font-medium">Admin</Link>
              <Link href="/cart" onClick={() => setMobileOpen(false)} className="block text-dark hover:text-rose-gold font-medium">
                Cart ({totalItems})
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
