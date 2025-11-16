import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sitemap - Elbey Projects",
  description: "Complete sitemap for Elbey Projects mobile mechanic website. Find all our pages and services.",
};

export default function Sitemap() {
  const pages = [
    { name: "Home", url: "/", description: "Welcome to Elbey Projects - Mobile Auto Repair" },
    { name: "About", url: "/about", description: "Learn about our 15+ years of experience" },
    { name: "Services", url: "/services", description: "Complete list of our automotive services" },
    { name: "Gallery", url: "/gallery", description: "Before and after photos of our work" },
    { name: "Contact", url: "/contact", description: "Book a service or get in touch" },
    { name: "FAQ", url: "/faq", description: "Frequently asked questions" },
    { name: "Blog", url: "/blog", description: "Auto repair tips and industry news" },
    { name: "Privacy Policy", url: "/privacy", description: "Our privacy policy and data handling" },
    { name: "Terms of Service", url: "/terms", description: "Terms and conditions for our services" },
  ];

  const services = [
    "Oil Changes",
    "Brake Repair",
    "Battery Replacement",
    "Tire Services",
    "Engine Diagnostics",
    "Transmission Service",
    "Cooling System Repair",
    "Electrical System Repair",
    "Suspension & Steering",
    "Exhaust System Repair",
    "Air Conditioning Service",
    "Emergency Roadside Assistance"
  ];

  return (
    <main className="min-h-screen bg-black text-white">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold mb-8 text-white">Sitemap</h1>

        <div className="grid md:grid-cols-2 gap-8">
          <section>
            <h2 className="text-2xl font-semibold mb-6 text-white">Pages</h2>
            <div className="space-y-4">
              {pages.map((page) => (
                <div key={page.url} className="border border-gray-800 rounded-lg p-4 hover:border-red-600 transition-colors">
                  <a href={page.url} className="block">
                    <h3 className="text-lg font-medium text-white hover:text-red-400 transition-colors">
                      {page.name}
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">{page.description}</p>
                  </a>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-6 text-white">Services</h2>
            <div className="space-y-2">
              {services.map((service) => (
                <div key={service} className="border border-gray-800 rounded-lg p-3 hover:border-red-600 transition-colors">
                  <a href="/services" className="block">
                    <span className="text-gray-300 hover:text-red-400 transition-colors">
                      {service}
                    </span>
                  </a>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold mb-6 text-white">Quick Links</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="/contact" className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-center transition-colors">
              Book Service
            </a>
            <a href="tel:+15551234567" className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-center transition-colors">
              Call Now
            </a>
            <a href="/gallery" className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-center transition-colors">
              View Gallery
            </a>
            <a href="/faq" className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-center transition-colors">
              FAQ
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
