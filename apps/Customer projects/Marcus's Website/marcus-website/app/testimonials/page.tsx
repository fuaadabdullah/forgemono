import Link from "next/link";
import { testimonials } from "@/data/testimonials";
import { Star } from "lucide-react";

export const metadata = {
  title: "Testimonials - Elbey Projects",
  description: "Read honest customer reviews and experiences with Elbey Projects mobile mechanic service.",
};

export default function TestimonialsPage() {
  return (
    <main className="min-h-screen bg-black text-white py-16">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Customer Testimonials</h1>
          <p className="text-gray-300 text-lg">Real feedback from our customers across service types and vehicle makes.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((t, i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-6 border border-gray-800">
              <div className="flex mb-4">
                {[...Array(t.rating)].map((_, j) => (
                  <Star key={j} className="w-5 h-5 text-yellow-400 fill-current" />
                ))}
              </div>

              <blockquote className="text-gray-300 mb-4 italic">"{t.text}"</blockquote>

              <div className="border-t border-gray-700 pt-4">
                <div className="font-semibold text-white">{t.name}</div>
                <div className="text-red-400 text-sm font-medium">{t.service}</div>
                <div className="text-gray-400 text-sm">{t.vehicle}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <Link href="/" className="inline-flex items-center px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md transition-colors">
            Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
