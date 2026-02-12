import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy - Elbey Projects",
  description: "Privacy policy for Elbey Projects mobile mechanic services. Learn how we protect and handle your personal information.",
};

export default function Privacy() {
  return (
    <main className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold mb-8 text-white">Privacy Policy</h1>

        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300 mb-6">
            Last updated: November 16, 2025
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Information We Collect</h2>
            <p className="text-gray-300 mb-4">
              We collect information you provide directly to us, such as when you:
            </p>
            <ul className="list-disc pl-6 text-gray-300 space-y-2">
              <li>Book a service or contact us</li>
              <li>Create an account or submit a form</li>
              <li>Communicate with us via phone, email, or our website</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">How We Use Your Information</h2>
            <p className="text-gray-300 mb-4">
              We use the information we collect to:
            </p>
            <ul className="list-disc pl-6 text-gray-300 space-y-2">
              <li>Provide and improve our services</li>
              <li>Communicate with you about your service requests</li>
              <li>Send you updates and marketing communications (with your consent)</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Information Sharing</h2>
            <p className="text-gray-300 mb-4">
              We do not sell, trade, or otherwise transfer your personal information to third parties without your consent,
              except as described in this policy or as required by law.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Data Security</h2>
            <p className="text-gray-300 mb-4">
              We implement appropriate security measures to protect your personal information against unauthorized access,
              alteration, disclosure, or destruction.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Contact Us</h2>
            <p className="text-gray-300 mb-4">
              If you have any questions about this Privacy Policy, please contact us at:
            </p>
            <div className="bg-gray-900 p-4 rounded-lg">
              <p className="text-gray-300">Email: privacy@elbeyprojects.com</p>
              <p className="text-gray-300">Phone: (555) 123-4567</p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
