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
    name: "Ayesha Khan",
    city: "Karachi",
    text: "Absolutely stunning necklace! The gold finish looks so premium. Got so many compliments at my cousin's wedding.",
    rating: 5,
  },
  {
    name: "Fatima Ali",
    city: "Lahore",
    text: "The quality is incredible for the price. My chandelier earrings look like real jewellery. Royal Sparkle is my go-to now!",
    rating: 5,
  },
  {
    name: "Sana Ahmed",
    city: "Islamabad",
    text: "Fast delivery and beautiful packaging. The bracelet I ordered is so delicate and elegant. Perfect everyday accessory.",
    rating: 4,
  },
];

const categoryImages: Record<string, string> = {
  bracelets: "/products/bracelets/bracelet-01.jpg",
  earrings: "/products/earrings/earring-01.jpg",
  necklaces: "/products/necklaces/necklace-01.jpg",
  rings: "/products/rings/ring-01.jpg",
  anklets: "/products/anklets/anklet-01.jpg",
  "hair-accessories": "/products/hair-accessories/hair-accessory-01.jpg",
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

  const newArrivals = [...allProducts]
    .sort((a, b) => b.id - a.id)
    .slice(0, 4);

  return (
    <div>
      {/* ───────────────────────────────────────────────────────────────────
          1. FULL-SCREEN HERO
      ─────────────────────────────────────────────────────────────────── */}
      <section className="relative h-screen w-full overflow-hidden">
        {/* Background Image */}
        <Image
          src="/products/necklaces/necklace-02.jpg"
          alt="Luxury Jewellery Collection"
          fill
          className="object-cover"
          priority
        />

        {/* Dark gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-dark/95 via-dark/70 to-dark/30" />

        {/* Decorative golden silk wave */}
        <div className="absolute inset-0 opacity-20">
          <svg viewBox="0 0 1440 900" className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <path d="M0,450 C360,300 720,600 1440,350 L1440,900 L0,900 Z" fill="url(#goldGrad)" />
            <defs>
              <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#C9A84C" stopOpacity="0.3" />
                <stop offset="50%" stopColor="#E8D48B" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#C9A84C" stopOpacity="0.05" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Content */}
        <div className="relative z-10 h-full flex items-center">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div className="max-w-2xl">
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-gold font-medium tracking-[0.3em] uppercase text-xs mb-6"
              >
                Premium Artificial Jewellery
              </motion.p>

              <motion.h1
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.9, delay: 0.4 }}
                className="text-5xl sm:text-6xl lg:text-8xl font-bold text-white leading-[1.05] mb-6"
              >
                MAKE A
                <span className="block text-gold italic">Jewellery</span>
                <span className="block text-3xl sm:text-4xl lg:text-5xl text-white/70 font-normal mt-2">Statement</span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.7 }}
                className="text-white/50 text-base sm:text-lg mb-10 max-w-md leading-relaxed"
              >
                Discover our exquisite bridal and everyday collection — handcrafted
                artificial jewellery designed for the woman who sparkles from within.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.9 }}
                className="flex gap-4 flex-wrap"
              >
                <Link
                  href="/shop"
                  className="bg-gold text-dark px-10 py-4 rounded-none font-medium text-sm tracking-[0.15em] uppercase hover:bg-gold-light transition-all duration-300 shadow-[0_4px_20px_rgba(201,168,76,0.3)]"
                >
                  Shop Now
                </Link>
                <Link
                  href="/shop"
                  className="border border-white/30 text-white px-10 py-4 rounded-none font-medium text-sm tracking-[0.15em] uppercase hover:border-gold hover:text-gold transition-all duration-300"
                >
                  Explore Collection
                </Link>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Side image thumbnails (like the reference) */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay: 1 }}
          className="absolute right-8 top-1/2 -translate-y-1/2 hidden xl:flex flex-col gap-3 z-10"
        >
          {[
            "/products/rings/ring-01.jpg",
            "/products/earrings/earring-02.jpg",
            "/products/bracelets/bracelet-03.jpg",
          ].map((src, i) => (
            <div
              key={i}
              className={`relative w-20 h-20 rounded-lg overflow-hidden border-2 ${
                i === 0 ? "border-gold" : "border-white/20"
              } cursor-pointer hover:border-gold transition-colors`}
            >
              <Image src={src} alt="" fill className="object-cover" />
            </div>
          ))}
          <div className="text-center mt-2">
            <span className="text-gold font-[family-name:var(--font-heading)] text-xl font-bold">01</span>
            <span className="text-white/30 text-sm"> / 03</span>
          </div>
        </motion.div>

        {/* Bottom scroll indicator */}
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
        >
          <div className="w-6 h-10 rounded-full border border-white/30 flex justify-center pt-2">
            <div className="w-1 h-2 bg-gold rounded-full" />
          </div>
        </motion.div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          2. EXPLORE BY CATEGORY (cream background like reference)
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-cream">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="w-12 h-px bg-dark/20" />
              <p className="text-dark/50 text-xs tracking-[0.3em] uppercase font-medium">
                Browse
              </p>
              <div className="w-12 h-px bg-dark/20" />
            </div>
            <h2 className="text-3xl lg:text-5xl font-bold text-dark">
              Explore by Category
            </h2>
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-3 lg:grid-cols-6 gap-6 sm:gap-8">
              {categories.map((cat, index) => (
                <motion.div
                  key={cat.id}
                  initial={{ opacity: 0, y: 25 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link
                    href={`/shop?category=${cat.slug}`}
                    className="group flex flex-col items-center"
                  >
                    <div className="relative w-20 h-20 sm:w-28 sm:h-28 rounded-full overflow-hidden border-2 border-dark/10 group-hover:border-gold transition-all duration-300 shadow-md group-hover:shadow-[0_8px_25px_rgba(201,168,76,0.2)] mb-4">
                      <Image
                        src={categoryImages[cat.slug] || "/products/necklaces/necklace-01.jpg"}
                        alt={cat.name}
                        fill
                        className="object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                    </div>
                    <h3 className="font-[family-name:var(--font-heading)] font-semibold text-dark group-hover:text-gold-dark transition-colors text-sm sm:text-base">
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
          3. FEATURED PRODUCTS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Curated for You
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
              Featured Collection
            </h2>
            <div className="w-16 h-0.5 bg-gold/40 mx-auto" />
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
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
              className="border border-gold text-gold px-10 py-4 rounded-none font-medium text-sm tracking-[0.15em] uppercase hover:bg-gold hover:text-dark transition-all duration-300 inline-block"
            >
              View All Products
            </Link>
          </div>
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          4. BANNER / PROMO SECTION
      ─────────────────────────────────────────────────────────────────── */}
      <section className="relative h-[50vh] overflow-hidden">
        <Image
          src="/products/earrings/earring-03.jpg"
          alt="Luxury Collection"
          fill
          className="object-cover"
        />
        <div className="absolute inset-0 bg-dark/70" />
        <div className="relative z-10 h-full flex items-center justify-center text-center px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <p className="text-gold text-xs tracking-[0.3em] uppercase font-medium mb-4">
              Limited Collection
            </p>
            <h2 className="text-4xl lg:text-6xl font-bold text-white mb-6 max-w-3xl">
              Elegance in Every Detail
            </h2>
            <Link
              href="/shop"
              className="bg-gold text-dark px-10 py-4 rounded-none font-medium text-sm tracking-[0.15em] uppercase hover:bg-gold-light transition-all duration-300 inline-block"
            >
              Shop the Collection
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ───────────────────────────────────────────────────────────────────
          5. NEW ARRIVALS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Just Dropped
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
              New Arrivals
            </h2>
            <div className="w-16 h-0.5 bg-gold/40 mx-auto" />
          </motion.div>

          {loading ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
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
          6. CUSTOMER REVIEWS
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-cream">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-dark/40 text-xs tracking-[0.3em] uppercase font-medium mb-3">
              Testimonials
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              What Our Customers Say
            </h2>
            <div className="w-16 h-0.5 bg-gold mx-auto" />
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {reviews.map((review, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="bg-white p-8 rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.06)] relative"
              >
                <span className="absolute top-4 right-6 text-5xl text-gold/15 font-[family-name:var(--font-heading)] leading-none">
                  &ldquo;
                </span>

                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span
                      key={i}
                      className={`text-sm ${i < review.rating ? "text-gold" : "text-dark/15"}`}
                    >
                      &#9733;
                    </span>
                  ))}
                </div>

                <p className="text-dark/60 leading-relaxed mb-6 text-sm">
                  &ldquo;{review.text}&rdquo;
                </p>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gold/20 flex items-center justify-center">
                    <span className="text-gold font-bold text-sm">{review.name[0]}</span>
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
          7. INSTAGRAM GALLERY
      ─────────────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-gold text-xs tracking-[0.3em] uppercase font-medium mb-3">
              @royalsparkle
            </p>
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
              Follow Us on Instagram
            </h2>
            <div className="w-16 h-0.5 bg-gold/40 mx-auto" />
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { src: "/products/necklaces/necklace-01.jpg", alt: "Bridal jewellery set" },
              { src: "/products/necklaces/necklace-03.jpg", alt: "Layered necklaces" },
              { src: "/products/earrings/earring-01.jpg", alt: "Statement earrings" },
              { src: "/products/bracelets/bracelet-01.jpg", alt: "Gold bangles" },
              { src: "/products/rings/ring-01.jpg", alt: "Ring collection" },
              { src: "/products/hair-accessories/hair-accessory-01.jpg", alt: "Hair accessories" },
            ].map((post, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="relative aspect-square rounded-xl overflow-hidden group cursor-pointer border border-gold/10"
              >
                <Image
                  src={post.src}
                  alt={post.alt}
                  fill
                  className="object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gold/0 group-hover:bg-gold/30 transition-all duration-300 flex items-center justify-center">
                  <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-2xl">
                    &#9829;
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
