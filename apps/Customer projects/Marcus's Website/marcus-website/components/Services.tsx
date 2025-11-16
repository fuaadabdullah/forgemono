"use client";

import { Button } from "@/components/ui/Button";

const services = [
  {
    title: "Brake Service",
    description: "Complete brake inspection, pad replacement, and rotor resurfacing. Safety first.",
    price: "From $89"
  },
  {
    title: "Oil Change",
    description: "Full synthetic oil changes with filter replacement. All vehicles welcome.",
    price: "From $39"
  },
  {
    title: "Diagnostics",
    description: "Advanced diagnostic scanning to identify issues before they become major problems.",
    price: "From $79"
  },
  {
    title: "Suspension Repair",
    description: "Shock absorber replacement, alignment, and suspension component repairs.",
    price: "From $149"
  },
  {
    title: "Mobile Repair",
    description: "We come to you! Emergency repairs and maintenance at your location.",
    price: "Service call $49"
  }
];

export default function Services() {
  return (
    <section className="py-16 bg-black">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-white">
          Our Services
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, index) => (
            <div key={index} className="bg-gray-900 rounded-lg p-6 border border-gray-800 hover:border-red-600 transition-colors">
              <h3 className="text-xl font-semibold mb-2 text-white">{service.title}</h3>
              <p className="text-gray-300 mb-4">{service.description}</p>
              <div className="flex justify-between items-center">
                <span className="text-red-400 font-semibold">{service.price}</span>
                <Button
                  size="sm"
                  className="bg-red-600 hover:bg-red-700 text-white"
                  onClick={() => {
                    document.getElementById('booking')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  Book Now
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button
            size="lg"
            className="bg-red-600 hover:bg-red-700 text-white px-8 py-4"
            onClick={() => {
              document.getElementById('booking')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            View All Services
          </Button>
        </div>
      </div>
    </section>
  );
}
