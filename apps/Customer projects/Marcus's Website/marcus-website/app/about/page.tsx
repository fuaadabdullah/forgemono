import { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Elbey Projects - 15 Years of Mobile Mechanic Experience",
  description: "Learn about Marcus and his 15 years of hands-on mechanic experience in Saudi Arabia. Honest, reliable mobile auto repair services.",
};

export default function About() {
  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            About Elbey Projects
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            15 years of honest, hands-on mechanic experience
          </p>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center mb-16">
            {/* Image placeholder */}
            <div className="bg-gray-800 rounded-lg h-96 flex items-center justify-center">
              <span className="text-gray-400">Marcus at work</span>
            </div>

            <div>
              <h2 className="text-3xl font-bold mb-6 text-white">My Story</h2>
              <div className="space-y-4 text-gray-300">
                <p>
                  My journey as a mechanic began 15 years ago in Saudi Arabia, where I learned the importance of
                  honest work and genuine customer relationships. What started as a passion for cars has evolved
                  into a commitment to providing reliable, transparent auto repair services.
                </p>
                <p>
                  I've seen it all – from simple oil changes to complex engine rebuilds. My experience spans
                  working in busy garages, mobile repair services, and even owning my own shop. Each experience
                  taught me valuable lessons about what customers truly need: honesty, reliability, and fair pricing.
                </p>
                <p>
                  When I moved to start Elbey Projects, I made a promise to myself and my customers – no unnecessary
                  repairs, no inflated prices, and no cutting corners. Every job gets the same attention to detail,
                  whether it's a brake pad replacement or a full engine service.
                </p>
              </div>
            </div>
          </div>

          {/* Experience & Values */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">15+</span>
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">Years Experience</h3>
              <p className="text-gray-300">Hands-on mechanic since 2010</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">1000+</span>
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">Vehicles Repaired</h3>
              <p className="text-gray-300">All makes and models serviced</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">24/7</span>
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">Emergency Service</h3>
              <p className="text-gray-300">Available when you need us most</p>
            </div>
          </div>

          {/* Why Choose Us */}
          <div className="bg-gray-900 rounded-lg p-8 border border-gray-800">
            <h2 className="text-3xl font-bold mb-6 text-white text-center">Why Customers Choose Elbey Projects</h2>

            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-semibold mb-3 text-white">Honest Diagnostics</h3>
                <p className="text-gray-300 mb-4">
                  I believe in transparency. You'll always know exactly what's wrong with your vehicle and why
                  it needs repair. No surprises, no hidden agendas.
                </p>

                <h3 className="text-xl font-semibold mb-3 text-white">Fair Pricing</h3>
                <p className="text-gray-300 mb-4">
                  Competitive rates based on the actual work needed, not inflated shop prices. I stand behind
                  my work with a satisfaction guarantee.
                </p>
              </div>

              <div>
                <h3 className="text-xl font-semibold mb-3 text-white">Mobile Service</h3>
                <p className="text-gray-300 mb-4">
                  I come to you. Whether you're at home, work, or stranded on the side of the road, I'll bring
                  the shop to your location.
                </p>

                <h3 className="text-xl font-semibold mb-3 text-white">Quality Workmanship</h3>
                <p className="text-gray-300 mb-4">
                  Every repair is done right the first time. I use genuine parts and proven techniques to ensure
                  your vehicle is safe and reliable.
                </p>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center mt-16">
            <h2 className="text-2xl font-bold mb-4 text-white">Ready to Experience the Difference?</h2>
            <p className="text-gray-300 mb-8">
              Contact me today for honest, reliable auto repair services.
            </p>
            <a
              href="/#booking"
              className="inline-flex items-center px-8 py-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md transition-colors"
            >
              Book Your Service
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
