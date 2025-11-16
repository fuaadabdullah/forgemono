import { Metadata } from "next";
import Contact from "@/components/Contact";

export const metadata: Metadata = {
  title: "Contact Us - Elbey Projects Mobile Mechanic",
  description: "Get in touch with Elbey Projects for mobile mechanic services. Book your service online or call us directly. 24/7 emergency service available.",
};

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Contact Us
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Ready to get your vehicle back on the road? Let's talk about your service needs.
          </p>
        </div>
      </section>

      {/* Contact Form */}
      <Contact />

      {/* Additional Contact Info */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Multiple Ways to Reach Us</h2>
            <p className="text-gray-300 text-lg">
              Choose the method that works best for you
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-black rounded-lg p-6 border border-gray-800 text-center">
              <div className="text-4xl mb-4">📞</div>
              <h3 className="text-xl font-semibold text-white mb-2">Phone</h3>
              <p className="text-gray-300 mb-4">Call us directly for immediate assistance</p>
              <a
                href="tel:+15551234567"
                className="text-red-400 hover:text-red-300 font-semibold"
              >
                (555) 123-4567
              </a>
              <p className="text-sm text-gray-400 mt-2">24/7 Emergency Line</p>
            </div>

            <div className="bg-black rounded-lg p-6 border border-gray-800 text-center">
              <div className="text-4xl mb-4">📧</div>
              <h3 className="text-xl font-semibold text-white mb-2">Email</h3>
              <p className="text-gray-300 mb-4">Send us details about your vehicle and service needs</p>
              <a
                href="mailto:service@elbeyprojects.com"
                className="text-red-400 hover:text-red-300 font-semibold"
              >
                service@elbeyprojects.com
              </a>
              <p className="text-sm text-gray-400 mt-2">Response within 2 hours</p>
            </div>

            <div className="bg-black rounded-lg p-6 border border-gray-800 text-center">
              <div className="text-4xl mb-4">📍</div>
              <h3 className="text-xl font-semibold text-white mb-2">Service Area</h3>
              <p className="text-gray-300 mb-4">We come to you! Mobile service within 25 miles</p>
              <span className="text-red-400 font-semibold">Greater Metro Area</span>
              <p className="text-sm text-gray-400 mt-2">Home, Office, or Roadside</p>
            </div>

            <div className="bg-black rounded-lg p-6 border border-gray-800 text-center">
              <div className="text-4xl mb-4">🕒</div>
              <h3 className="text-xl font-semibold text-white mb-2">Hours</h3>
              <p className="text-gray-300 mb-4">Flexible scheduling to fit your needs</p>
              <span className="text-red-400 font-semibold">Mon-Sun: 7AM-9PM</span>
              <p className="text-sm text-gray-400 mt-2">Emergency service 24/7</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
