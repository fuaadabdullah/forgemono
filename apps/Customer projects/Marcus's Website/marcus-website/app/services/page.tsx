import { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Auto Repair Services - Elbey Projects Mobile Mechanic",
  description: "Professional mobile mechanic services: brakes, oil changes, diagnostics, suspension, engine service. We come to you for all your auto repair needs.",
};

const services = [
  {
    id: "brakes",
    title: "Brake Service & Repair",
    description: "Complete brake system inspection, pad replacement, rotor resurfacing, and fluid flush. Safety is our top priority.",
    features: ["Brake pad replacement", "Rotor inspection & resurfacing", "Brake fluid flush", "Emergency brake adjustment"],
    price: "From $89",
    image: "/images/brake-service.jpg"
  },
  {
    id: "diagnostics",
    title: "Advanced Diagnostics",
    description: "Using the latest diagnostic equipment to identify issues before they become major problems. OBD-II scanning and troubleshooting.",
    features: ["OBD-II scanning", "Check engine light diagnosis", "Electrical system testing", "Performance analysis"],
    price: "From $79",
    image: "/images/diagnostics.jpg"
  },
  {
    id: "oil-change",
    title: "Oil Change Service",
    description: "Full synthetic oil changes with premium filters. All vehicles welcome, including diesel and European models.",
    features: ["Full synthetic oil", "Premium oil filter", "Multi-grade options", "Fluid level check"],
    price: "From $39",
    image: "/images/oil-change.jpg"
  },
  {
    id: "suspension",
    title: "Suspension & Steering",
    description: "Shock absorber replacement, alignment, and complete suspension component repairs for a smooth, safe ride.",
    features: ["Shock/strut replacement", "Wheel alignment", "Ball joint replacement", "Control arm service"],
    price: "From $149",
    image: "/images/suspension.jpg"
  },
  {
    id: "engine",
    title: "Engine Service & Repair",
    description: "Complete engine diagnostics, maintenance, and repair. From tune-ups to major rebuilds, we handle it all.",
    features: ["Engine diagnostics", "Timing belt service", "Tune-ups", "Cooling system service"],
    price: "From $99",
    image: "/images/engine-service.jpg"
  },
  {
    id: "mobile",
    title: "Mobile Repair Service",
    description: "Emergency roadside assistance and mobile repairs. We come to you - home, office, or breakdown location.",
    features: ["24/7 emergency service", "Mobile diagnostics", "On-site repairs", "Towing coordination"],
    price: "Service call $49",
    image: "/images/mobile-repair.jpg"
  }
];

export default function Services() {
  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Our Services
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Professional mobile mechanic services for all your automotive needs
          </p>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service) => (
              <div key={service.id} className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800 hover:border-red-600 transition-colors">
                {/* Service Image Placeholder */}
                <div className="h-48 bg-gray-800 flex items-center justify-center">
                  <span className="text-gray-400">{service.title}</span>
                </div>

                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-2 text-white">{service.title}</h3>
                  <p className="text-gray-300 mb-4">{service.description}</p>

                  <div className="mb-4">
                    <h4 className="font-semibold text-white mb-2">Includes:</h4>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {service.features.map((feature, index) => (
                        <li key={index} className="flex items-center">
                          <span className="w-1.5 h-1.5 bg-red-600 rounded-full mr-2"></span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-red-400 font-semibold">{service.price}</span>
                    <Link href="/#booking">
                      <Button
                        size="sm"
                        className="bg-red-600 hover:bg-red-700 text-white"
                      >
                        Book Now
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Additional Services */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Additional Services</h2>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div className="bg-black rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-semibold mb-3 text-white">Pre-Purchase Inspection</h3>
              <p className="text-gray-300 mb-4">
                Comprehensive vehicle inspection before purchase. Peace of mind for your investment.
              </p>
              <p className="text-red-400 font-semibold">From $149</p>
            </div>

            <div className="bg-black rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-semibold mb-3 text-white">Maintenance Packages</h3>
              <p className="text-gray-300 mb-4">
                Scheduled maintenance plans to keep your vehicle running smoothly and prevent breakdowns.
              </p>
              <p className="text-red-400 font-semibold">Custom pricing</p>
            </div>
          </div>

          <div className="bg-red-600 rounded-lg p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">Need Something Else?</h3>
            <p className="mb-6">
              We handle all types of auto repairs and maintenance. If you don't see your service listed,
              contact us and we'll be happy to help.
            </p>
            <Link href="/#booking">
              <Button
                size="lg"
                className="bg-white text-red-600 hover:bg-gray-100"
              >
                Contact Us
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
