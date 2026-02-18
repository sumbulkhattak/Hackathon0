"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Product } from "@/lib/types";
import { useCart } from "./CartProvider";

export default function ProductCard({ product }: { product: Product }) {
  const { addToCart } = useCart();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="bg-surface rounded-2xl shadow-[0_4px_20px_rgba(201,168,76,0.08)] hover:shadow-[0_8px_30px_rgba(201,168,76,0.18)] transition-all duration-300 overflow-hidden group border border-gold/10 hover:border-gold/25"
    >
      <Link href={`/product/${product.slug}`}>
        <div className="relative aspect-square overflow-hidden bg-dark">
          <Image
            src={product.image_url}
            alt={product.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-500"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          {product.featured && (
            <span className="absolute top-3 left-3 bg-gold text-dark text-xs px-3 py-1 rounded-full font-medium">
              Featured
            </span>
          )}
        </div>
      </Link>

      <div className="p-4">
        <p className="text-xs text-gold font-medium uppercase tracking-wider mb-1">
          {product.category_name}
        </p>
        <Link href={`/product/${product.slug}`}>
          <h3 className="font-[family-name:var(--font-heading)] font-semibold text-white hover:text-gold transition-colors">
            {product.name}
          </h3>
        </Link>
        <div className="flex items-center justify-between mt-3">
          <span className="text-lg font-bold text-gold-dark">
            Rs.{product.price.toLocaleString("en-IN")}
          </span>
          <button
            onClick={() => addToCart(product)}
            className="bg-gold text-dark px-4 py-2 rounded-full text-sm font-medium hover:bg-gold-light transition-all duration-300 shadow-[0_4px_20px_rgba(201,168,76,0.15)] hover:shadow-[0_8px_30px_rgba(201,168,76,0.25)]"
          >
            Add to Cart
          </button>
        </div>
      </div>
    </motion.div>
  );
}
