import { DollarSign, Shield, Truck } from "lucide-react";

const features = [
  {
    icon: DollarSign,
    title: "Fair Pricing",
    description: "Transparent pricing with no hidden fees. Get the best value for your money."
  },
  {
    icon: Shield,
    title: "Honest Service",
    description: "15 years of experience with honest diagnostics and recommendations."
  },
  {
    icon: Truck,
    title: "Mobile & Reliable",
    description: "We come to you. Fast response times and reliable service you can count on."
  }
];

export default function WhyUs() {
  return (
    <section className="py-16 bg-gray-900">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-white">
          Why Choose Elbey Projects?
        </h2>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center">
                <feature.icon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">{feature.title}</h3>
              <p className="text-gray-300">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
