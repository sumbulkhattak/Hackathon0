"use client";

import Link from "next/link";
import { useCart } from "./CartProvider";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Navbar() {
  const { totalItems } = useCart();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-dark/95 backdrop-blur-md shadow-[0_2px_20px_rgba(0,0,0,0.3)]"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-[family-name:var(--font-heading)] text-2xl font-bold text-white tracking-wider uppercase">
              Royal Sparkle
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-10">
            <Link
              href="/"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Home
            </Link>
            <Link
              href="/shop"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Shop
            </Link>
            <Link
              href="/shop?category=necklaces"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Necklaces
            </Link>
            <Link
              href="/shop?category=rings"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Rings
            </Link>
            <Link
              href="/shop?category=earrings"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Earrings
            </Link>
            <Link
              href="/admin"
              className="text-white/80 hover:text-gold transition-colors duration-300 text-sm font-medium tracking-wide uppercase"
            >
              Admin
            </Link>
          </div>

          {/* Right side */}
          <div className="hidden md:flex items-center space-x-5">
            <Link
              href="/cart"
              className="relative text-white/80 hover:text-gold transition-colors duration-300"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
                />
              </svg>
              {totalItems > 0 && (
                <span className="absolute -top-2 -right-2 bg-gold text-dark text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                  {totalItems}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-white"
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
            className="md:hidden bg-dark/95 backdrop-blur-md border-t border-gold/15 overflow-hidden"
          >
            <div className="px-4 py-3 space-y-3">
              <Link href="/" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Home</Link>
              <Link href="/shop" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Shop</Link>
              <Link href="/shop?category=necklaces" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Necklaces</Link>
              <Link href="/shop?category=rings" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Rings</Link>
              <Link href="/shop?category=earrings" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Earrings</Link>
              <Link href="/admin" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">Admin</Link>
              <Link href="/cart" onClick={() => setMobileOpen(false)} className="block text-white/80 hover:text-gold font-medium">
                Cart ({totalItems})
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
