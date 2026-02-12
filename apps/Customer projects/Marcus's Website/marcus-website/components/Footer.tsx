import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-gray-900 border-t border-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <picture>
                <source srcSet="/images/elbeylogo.avif 1x, /images/elbeylogo.avif 2x" type="image/avif" />
                <source srcSet="/images/elbeylogo-256.webp 1x, /images/elbeylogo.webp 2x" type="image/webp" />
                <img
                  src="/images/elbeylogo.jpg"
                  srcSet="/images/elbeylogo-256.webp 256w, /images/elbeylogo.webp 512w"
                  alt="Elbey Projects Logo"
                  className="w-8 h-8"
                  loading="lazy"
                  width={32}
                  height={32}
                />
              </picture>
              <span className="text-lg font-bold text-white">Elbey Projects</span>
            </div>
            <p className="text-gray-400 text-sm mb-4">
              Professional mobile mechanic services. 15 years of hands-on experience.
            </p>
            <div className="space-y-2 text-sm text-gray-400">
              <p>📍 Mobile Service - Serving Greater Metro Area</p>
              <p>📞 (555) 123-4567</p>
              <p>✉️ info@elbeyprojects.com</p>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <div className="space-y-2">
              <Link href="/about" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                About Us
              </Link>
              <Link href="/services" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Services
              </Link>
              <Link href="/gallery" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Gallery
              </Link>
              <Link href="/contact" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Contact
              </Link>
            </div>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-white font-semibold mb-4">Services</h3>
            <div className="space-y-2">
              <Link href="/services" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Oil Changes
              </Link>
              <Link href="/services" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Brake Repair
              </Link>
              <Link href="/services" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Engine Service
              </Link>
              <Link href="/services" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Diagnostics
              </Link>
            </div>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <div className="space-y-2">
              <Link href="/privacy" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Privacy Policy
              </Link>
              <Link href="/terms" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Terms of Service
              </Link>
              <Link href="/faq" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                FAQ
              </Link>
              <Link href="/sitemap" className="block text-gray-400 hover:text-red-400 transition-colors text-sm">
                Sitemap
              </Link>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center">
          <p className="text-gray-400 text-sm">
            © {new Date().getFullYear()} Elbey Projects. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
