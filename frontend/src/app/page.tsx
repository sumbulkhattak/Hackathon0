"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { getProducts, getCategories } from "@/lib/api";
import { Product, Category } from "@/lib/types";
import ProductCard from "@/components/ProductCard";

const reviews = [
  {
    name: "Ananya Mehta",
    city: "Mumbai",
    text: "Absolutely stunning necklace! The rose-gold finish looks so premium. Got so many compliments at my cousin's wedding.",
    rating: 5,
    avatar: "https://picsum.photos/seed/avatar1/80/80",
  },
  {
    name: "Riya Kapoor",
    city: "Delhi",
    text: "The quality is incredible for the price. My chandelier earrings look like real jewellery. Royal Sparkle is my go-to now!",
    rating: 5,
    avatar: "https://picsum.photos/seed/avatar2/80/80",
  },
  {
    name: "Sneha Iyer",
    city: "Bangalore",
    text: "Fast delivery and beautiful packaging. The bracelet I ordered is so delicate and elegant. Perfect everyday accessory.",
    rating: 4,
    avatar: "https://picsum.photos/seed/avatar3/80/80",
  },
];

const instagramPosts = [
  { src: "https://picsum.photos/seed/insta1/400/400", alt: "Bridal jewellery set" },
  { src: "https://picsum.photos/seed/insta2/400/400", alt: "Layered necklaces" },
  { src: "https://picsum.photos/seed/insta3/400/400", alt: "Statement earrings" },
  { src: "https://picsum.photos/seed/insta4/400/400", alt: "Rose gold bangles" },
  { src: "https://picsum.photos/seed/insta5/400/400", alt: "Ring collection" },
  { src: "https://picsum.photos/seed/insta6/400/400", alt: "Hair accessories" },
];

const categoryIcons: Record<string, string> = {
  earrings: "✨",
  necklaces: "📿",
  bracelets: "💎",
  rings: "💍",
  anklets: "⭐",
  "hair-accessories": "🌸",
};

export default function HomePage() {
  const [featured, setFeatured] = useState<Product[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getProducts(undefined, true), getCategories(), getProducts()])
      .then(([featuredProducts, cats, all]) => {
        setFeatured(featuredProducts);
        setCategories(cats);
        setAllProducts(all);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // New Arrivals: last 4 products by ID (most recently added)
  const newArrivals = [...allProducts]
    .sort((a, b) => b.id - a.id)
    .slice(0, 4);

  return (
    <div>
      {/* ───────────────────────────────────────────────────────────────────
          1. HERO BANNER
      ─────────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blush via-cream to-beige min-h-[90vh] flex items-center">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center py-16">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          >
            <p className="text-rose-gold font-medium tracking-[0.25em] uppercase text-xs mb-5">
              Premium Artificial Jewellery
            </p>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-dark leading-[1.1] mb-6">
              Shine Like
              <span className="text-rose-gold block italic">Royalty</span>
            </h1>
            <p className="text-dark/55 text-lg mb-10 max-w-md leading-relaxed">
              Discover our exquisite bridal and everyday collection — handcrafted
              artificial jewellery designed for the woman who sparkles from within.
            </p>
            <div className="flex gap-4 flex-wrap">
              <Link
                href="/shop"
                className="bg-rose-gold text-white px-9 py-4 rounded-full font-medium text-sm tracking-wide uppercase hover:bg-rose-gold-dark transition-all duration-300 shadow-[0_4px_20px_rgba(183,110,121,0.15)] hover:shadow-[0_8px_30px_rgba(183,110,121,0.25)]"
              >
                Shop Now
              </Link>
              <Link
                href="/shop"
                className="border-2 border-rose-gold text-rose-gold px-9 py-4 rounded-full font-medium text-sm tracking-wide uppercase hover:bg-rose-gold hover:text-white transition-all duration-300"
              >
                Bridal Collection
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
            className="relative hidden lg:block"
          >
            <div className="relative w-full max-w-xl mx-auto">
              {/* Decorative ring behind image */}
              <div className="absolute -inset-6 border-2 border-rose-gold/20 rounded-full" />
              <div className="absolute -inset-12 border border-rose-gold/10 rounded-full" />
              <div className="relative aspect-square rounded-full overflow-hidden shadow-[0_20px_60px_rgba(183,110,121,0.25)]">
                <Image
                  src="https://picsum.photos/seed/bridal-jewellery/600/600"
                  alt="Bridal Jewellery Collection"
                  fill
                  className="object-cover"
                  priority
                />
              </div>
              {/* Floating badge */}
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -bottom-2 -left-4 bg-white px-5 py-3 rounded-2xl shadow-[0_8px_30px_rgba(183,110,121,0.15)]"
              >
                <p className="text-xs text-dark/50">Trusted by</p>
                <p className="font-[family-name:var(--font-heading)] font-bold text-rose-gold-dark text-lg">10K+ Women</p>
              </motion.div>
              <motion.div
                animate={{ y: [0, 8, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -top-2 -right-4 bg-white px-5 py-3 rounded-2xl shadow-[0_8px_30px_rgba(183,110,121,0.15)]"
              >
                <p className="text-xs text-dark/50">Starting at</p>
                <p className="font-[family-name:var(--font-heading)] font-bold text-rose-gold-dark text-lg">₹299</p>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* Soft decorative blurs */}
        <div className="absolute top-16 left-8 w-24 h-24 bg-rose-gold/5 rounded-full blur-2xl" />
        <div className="absolute bottom-16 right-8 w-40 h-40 bg-rose-gold/5 rounded-full blur-2xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-rose-gold/3 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          2. FEATURED PRODUCTS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-rose-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Curated for You
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              Featured Collection
            </h2>
            <div className="w-16 h-0.5 bg-rose-gold/40 mx-auto" />
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-rose-gold border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featured.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          <div className="text-center mt-12">
            <Link
              href="/shop"
              className="border-2 border-rose-gold text-rose-gold px-8 py-3.5 rounded-full font-medium text-sm tracking-wide uppercase hover:bg-rose-gold hover:text-white transition-all duration-300 inline-block"
            >
              View All Products
            </Link>
          </div>
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          3. SHOP BY CATEGORY
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-gradient-to-b from-beige/40 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-rose-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Browse
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              Shop by Category
            </h2>
            <div className="w-16 h-0.5 bg-rose-gold/40 mx-auto" />
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-rose-gold border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-5">
              {categories.map((cat, index) => (
                <motion.div
                  key={cat.id}
                  initial={{ opacity: 0, y: 25 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.08 }}
                >
                  <Link
                    href={`/shop?category=${cat.slug}`}
                    className="block bg-white p-7 rounded-2xl text-center hover:shadow-[0_12px_40px_rgba(183,110,121,0.15)] transition-all duration-400 group border border-blush/50 hover:border-rose-gold/30"
                  >
                    <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                      {categoryIcons[cat.slug] || "💫"}
                    </div>
                    <h3 className="font-[family-name:var(--font-heading)] font-semibold text-dark group-hover:text-rose-gold transition-colors text-sm">
                      {cat.name}
                    </h3>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          4. NEW ARRIVALS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-rose-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Just Dropped
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              New Arrivals
            </h2>
            <div className="w-16 h-0.5 bg-rose-gold/40 mx-auto" />
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-rose-gold border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {newArrivals.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          5. CUSTOMER REVIEWS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-gradient-to-b from-blush/30 to-cream/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-rose-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Testimonials
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              What Our Customers Say
            </h2>
            <div className="w-16 h-0.5 bg-rose-gold/40 mx-auto" />
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {reviews.map((review, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="bg-white p-8 rounded-2xl shadow-[0_4px_20px_rgba(183,110,121,0.08)] border border-blush/30 relative"
              >
                {/* Quote mark */}
                <span className="absolute top-4 right-6 text-5xl text-rose-gold/10 font-[family-name:var(--font-heading)] leading-none">
                  &ldquo;
                </span>

                {/* Stars */}
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span
                      key={i}
                      className={`text-sm ${i < review.rating ? "text-rose-gold" : "text-dark/15"}`}
                    >
                      &#9733;
                    </span>
                  ))}
                </div>

                <p className="text-dark/60 leading-relaxed mb-6 text-sm">
                  &ldquo;{review.text}&rdquo;
                </p>

                <div className="flex items-center gap-3">
                  <div className="relative w-10 h-10 rounded-full overflow-hidden bg-beige">
                    <Image src={review.avatar} alt={review.name} fill className="object-cover" />
                  </div>
                  <div>
                    <p className="font-medium text-dark text-sm">{review.name}</p>
                    <p className="text-xs text-dark/40">{review.city}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          6. INSTAGRAM GALLERY
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-rose-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              @royalsparkle
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              Follow Us on Instagram
            </h2>
            <div className="w-16 h-0.5 bg-rose-gold/40 mx-auto" />
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {instagramPosts.map((post, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="relative aspect-square rounded-xl overflow-hidden group cursor-pointer"
              >
                <Image
                  src={post.src}
                  alt={post.alt}
                  fill
                  className="object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-rose-gold/0 group-hover:bg-rose-gold/30 transition-all duration-300 flex items-center justify-center">
                  <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-2xl">
                    &#9829;
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          7. FOOTER is in layout.tsx (global Footer component)
      ─────────────────────────────────────────────────────────────────── */}
    </div>
  );
}
