import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-darker text-white/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <h3 className="font-[family-name:var(--font-heading)] text-xl font-bold text-gold mb-3">
              ✦ Royal Sparkle
            </h3>
            <p className="text-sm text-white/50 leading-relaxed">
              Discover the elegance of premium artificial jewellery.
              Crafted with love, designed for the modern woman.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-[family-name:var(--font-heading)] font-semibold mb-3 text-white">Quick Links</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/" className="hover:text-gold transition-colors">Home</Link></li>
              <li><Link href="/shop" className="hover:text-gold transition-colors">Shop All</Link></li>
              <li><Link href="/cart" className="hover:text-gold transition-colors">My Cart</Link></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-[family-name:var(--font-heading)] font-semibold mb-3 text-white">Contact</h4>
            <ul className="space-y-2 text-sm text-white/50">
              <li>hello@royalsparkle.com</li>
              <li>+92 300 1234567</li>
              <li>Karachi, Pakistan</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gold/10 mt-8 pt-6 text-center text-xs text-white/40">
          &copy; {new Date().getFullYear()} Royal Sparkle. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
