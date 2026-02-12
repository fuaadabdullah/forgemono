"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

const faqs = [
  {
    question: "How quickly can you respond to service calls?",
    answer: "We offer same-day service for most repairs and emergency situations. For non-emergency services, we typically schedule within 1-2 business days. Emergency roadside assistance is available 24/7."
  },
  {
    question: "Do you provide mobile service or do I need to bring my vehicle to a shop?",
    answer: "We specialize in mobile mechanic services! We come to you - whether you're at home, work, or experiencing a breakdown. We bring all necessary tools and parts to complete most repairs on-site."
  },
  {
    question: "What is your service area?",
    answer: "We currently serve the greater metropolitan area and surrounding suburbs. Service calls within a 25-mile radius of our base location. Contact us to confirm if we service your specific location."
  },
  {
    question: "Do you offer warranties on your work?",
    answer: "Yes! We stand behind our work with a 12-month/12,000-mile warranty on parts and labor for most services. Specific warranty terms vary by service type."
  },
  {
    question: "What forms of payment do you accept?",
    answer: "We accept cash, credit cards (Visa, MasterCard, American Express), and digital payments. For larger jobs, we can arrange financing options. All major cards accepted."
  },
  {
    question: "Can you work on my specific make and model?",
    answer: "We service all makes and models of vehicles, including domestic, imported, diesel, and electric vehicles. Our diagnostic equipment works with all modern vehicles."
  },
  {
    question: "What should I expect during a typical service visit?",
    answer: "First, we'll discuss your vehicle's issues and perform a thorough inspection. We'll provide a detailed quote before beginning work. You'll receive regular updates during the service, and we'll explain what we found and fixed when complete."
  },
  {
    question: "Do you offer emergency roadside assistance?",
    answer: "Yes, we provide 24/7 emergency roadside assistance including jump starts, tire changes, towing coordination, and emergency repairs to get you safely to our shop or home."
  },
  {
    question: "How do you determine your pricing?",
    answer: "Our pricing is based on the actual work required, parts costs, and local market rates. We provide detailed quotes upfront with no hidden fees. We focus on fair, competitive pricing without cutting corners on quality."
  },
  {
    question: "What if I need parts that aren't in stock?",
    answer: "For most common parts, we carry them in our service van. For specialty parts, we can often source them locally or have them delivered within 1-2 business days. We'll discuss timing and options with you upfront."
  },
  {
    question: "Do you provide written estimates?",
    answer: "Absolutely! We provide detailed written estimates for all services before beginning work. This includes labor costs, parts, and any applicable taxes. No work begins without your approval."
  },
  {
    question: "What if I'm not satisfied with the service?",
    answer: "Your satisfaction is our priority. If you're not completely satisfied, we'll work with you to make it right. We offer a 30-day satisfaction guarantee on all our work."
  }
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <main className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <h1 className="text-4xl md:text-5xl font-bold text-center mb-4 text-white">
          Frequently Asked Questions
        </h1>
        <p className="text-xl text-center mb-12 text-gray-300">
          Everything you need to know about our mobile mechanic services
        </p>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="bg-gray-900 rounded-lg border border-gray-800">
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-800 transition-colors"
              >
                <span className="text-lg font-medium text-white">{faq.question}</span>
                {openIndex === index ? (
                  <ChevronUp className="w-5 h-5 text-red-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-red-400" />
                )}
              </button>
              {openIndex === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-400 mb-4">
            Still have questions? We're here to help!
          </p>
          <a
            href="/contact"
            className="inline-block bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
          >
            Contact Us
          </a>
        </div>
      </div>
    </main>
  );
}
