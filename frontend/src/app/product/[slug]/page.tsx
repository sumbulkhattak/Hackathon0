"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { getProduct } from "@/lib/api";
import { Product } from "@/lib/types";
import { useCart } from "@/components/CartProvider";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { addToCart } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    if (slug) {
      getProduct(slug)
        .then(setProduct)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [slug]);

  const handleAddToCart = () => {
    if (product) {
      addToCart(product, quantity);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-rose-gold border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <h2 className="text-2xl font-bold text-dark mb-4">Product Not Found</h2>
        <Link href="/shop" className="text-rose-gold hover:underline">
          Back to Shop
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen">
      {/* Breadcrumb */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <nav className="text-sm text-dark/40">
          <Link href="/" className="hover:text-rose-gold">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/shop" className="hover:text-rose-gold">Shop</Link>
          <span className="mx-2">/</span>
          <span className="text-dark">{product.name}</span>
        </nav>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Image Gallery */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Main Image */}
            <div className="relative aspect-square rounded-3xl overflow-hidden bg-beige shadow-[0_4px_20px_rgba(183,110,121,0.1)] mb-4">
              <Image
                src={
                  product.images?.length > 0
                    ? product.images[activeImage]
                    : product.image_url
                }
                alt={product.name}
                fill
                className="object-cover"
                priority
              />
              {product.featured && (
                <span className="absolute top-4 left-4 bg-rose-gold text-white text-sm px-4 py-1.5 rounded-full font-medium">
                  Featured
                </span>
              )}
            </div>

            {/* Thumbnail Strip */}
            {product.images?.length > 1 && (
              <div className="flex gap-3">
                {product.images.map((img, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveImage(index)}
                    className={`relative w-20 h-20 rounded-xl overflow-hidden border-2 transition-all duration-200 ${
                      activeImage === index
                        ? "border-rose-gold shadow-[0_4px_20px_rgba(183,110,121,0.2)]"
                        : "border-transparent opacity-60 hover:opacity-100"
                    }`}
                  >
                    <Image
                      src={img}
                      alt={`${product.name} view ${index + 1}`}
                      fill
                      className="object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </motion.div>

          {/* Details */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-col justify-center"
          >
            <p className="text-rose-gold font-medium uppercase tracking-widest text-sm mb-2">
              {product.category_name}
            </p>

            <h1 className="text-3xl lg:text-4xl font-bold text-dark mb-4">
              {product.name}
            </h1>

            <p className="text-dark/60 text-lg leading-relaxed mb-6">
              {product.description}
            </p>

            <div className="text-3xl font-bold text-rose-gold-dark mb-6">
              ₹{product.price.toLocaleString("en-IN")}
            </div>

            {/* Stock Status */}
            <div className="mb-6">
              {product.stock > 10 ? (
                <span className="text-green-600 text-sm font-medium">● In Stock</span>
              ) : product.stock > 0 ? (
                <span className="text-orange-500 text-sm font-medium">
                  ● Only {product.stock} left
                </span>
              ) : (
                <span className="text-red-500 text-sm font-medium">● Out of Stock</span>
              )}
            </div>

            {/* Quantity */}
            <div className="flex items-center gap-4 mb-8">
              <span className="text-dark/60 font-medium">Quantity:</span>
              <div className="flex items-center border border-blush rounded-full overflow-hidden">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="px-4 py-2 text-dark hover:bg-blush transition-colors"
                >
                  -
                </button>
                <span className="px-4 py-2 font-medium">{quantity}</span>
                <button
                  onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                  className="px-4 py-2 text-dark hover:bg-blush transition-colors"
                >
                  +
                </button>
              </div>
            </div>

            {/* Add to Cart */}
            <button
              onClick={handleAddToCart}
              disabled={product.stock === 0}
              className={`w-full sm:w-auto px-10 py-4 rounded-full font-medium text-lg transition-all duration-300 ${
                added
                  ? "bg-green-500 text-white"
                  : product.stock === 0
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-rose-gold text-white hover:bg-rose-gold-dark shadow-[0_4px_20px_rgba(183,110,121,0.1)] hover:shadow-[0_8px_30px_rgba(183,110,121,0.2)]"
              }`}
            >
              {added ? "Added to Cart!" : product.stock === 0 ? "Out of Stock" : "Add to Cart"}
            </button>

            {/* Features */}
            <div className="mt-10 pt-8 border-t border-blush">
              <div className="grid grid-cols-3 gap-4 text-center text-sm text-dark/50">
                <div>
                  <div className="text-2xl mb-1">🚚</div>
                  <p>Free Shipping</p>
                </div>
                <div>
                  <div className="text-2xl mb-1">🔄</div>
                  <p>Easy Returns</p>
                </div>
                <div>
                  <div className="text-2xl mb-1">💎</div>
                  <p>Premium Quality</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
