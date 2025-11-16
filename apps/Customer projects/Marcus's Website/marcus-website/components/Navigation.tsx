"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 w-full bg-black/90 backdrop-blur-sm z-50 border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
              <picture>
                <source srcSet="/images/elbeylogo-256.webp 256w, /images/elbeylogo.webp 512w" type="image/webp" />
                <source srcSet="/images/elbeylogo.avif 512w" type="image/avif" />
                <img
                  src="/images/elbeylogo.jpg"
                  srcSet="/images/elbeylogo-256.webp 256w, /images/elbeylogo.webp 512w"
                  alt="Elbey Projects Logo"
                  className="w-10 h-10"
                  loading="lazy"
                  width={40}
                  height={40}
                />
              </picture>
            <span className="text-xl font-bold text-white">Elbey Projects</span>
          </Link>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-300 hover:text-red-400 transition-colors">
              Home
            </Link>
            <Link href="/about" className="text-gray-300 hover:text-red-400 transition-colors">
              About
            </Link>
            <Link href="/services" className="text-gray-300 hover:text-red-400 transition-colors">
              Services
            </Link>
            <Link href="/gallery" className="text-gray-300 hover:text-red-400 transition-colors">
              Gallery
            </Link>
            <Link href="/contact" className="text-gray-300 hover:text-red-400 transition-colors">
              Contact
            </Link>
            <Link href="/faq" className="text-gray-300 hover:text-red-400 transition-colors">
              FAQ
            </Link>
            <Link href="/blog" className="text-gray-300 hover:text-red-400 transition-colors">
              Blog
            </Link>
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center space-x-4">
            <a href="tel:+15551234567" className="text-gray-300 hover:text-red-400 transition-colors">
              (555) 123-4567
            </a>
            <Link href="/contact" className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
              Book Service
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden text-white p-2"
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden mt-4 pb-4 border-t border-gray-800">
            <div className="flex flex-col space-y-4 pt-4">
              <Link
                href="/"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>
              <Link
                href="/about"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                About
              </Link>
              <Link
                href="/services"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Services
              </Link>
              <Link
                href="/gallery"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Gallery
              </Link>
              <Link
                href="/contact"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Contact
              </Link>
              <Link
                href="/faq"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                FAQ
              </Link>
              <Link
                href="/blog"
                className="text-gray-300 hover:text-red-400 transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                Blog
              </Link>

              <div className="pt-4 border-t border-gray-800 flex flex-col space-y-4">
                <a
                  href="tel:+15551234567"
                  className="text-gray-300 hover:text-red-400 transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  📞 (555) 123-4567
                </a>
                <Link
                  href="/contact"
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors text-center"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Book Service
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
