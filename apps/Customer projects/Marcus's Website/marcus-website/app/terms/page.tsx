import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service - Elbey Projects",
  description: "Terms of service for Elbey Projects mobile mechanic services. Read our terms and conditions for using our services.",
};

export default function Terms() {
  return (
    <main className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold mb-8 text-white">Terms of Service</h1>

        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300 mb-6">
            Last updated: November 16, 2025
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Acceptance of Terms</h2>
            <p className="text-gray-300 mb-4">
              By accessing and using Elbey Projects mobile mechanic services, you accept and agree to be bound by the terms
              and provision of this agreement.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Services</h2>
            <p className="text-gray-300 mb-4">
              Elbey Projects provides mobile automotive repair and maintenance services. All services are performed
              at the customer's location or designated service area.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Pricing and Payment</h2>
            <p className="text-gray-300 mb-4">
              Service pricing is provided upfront before work begins. Payment is due upon completion of services.
              We accept cash, credit cards, and approved digital payment methods.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Warranties</h2>
            <p className="text-gray-300 mb-4">
              Parts and labor are covered by manufacturer warranties where applicable. Elbey Projects provides
              a 30-day warranty on all repair work performed.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Liability</h2>
            <p className="text-gray-300 mb-4">
              Elbey Projects is not liable for incidental or consequential damages. Our liability is limited to
              the amount paid for services rendered.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Contact Information</h2>
            <div className="bg-gray-900 p-4 rounded-lg">
              <p className="text-gray-300">Email: info@elbeyprojects.com</p>
              <p className="text-gray-300">Phone: (555) 123-4567</p>
              <p className="text-gray-300">Address: Mobile Service - Serving Greater Metro Area</p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
