import { Metadata } from "next";
import { Play, Image as ImageIcon } from "lucide-react";

export const metadata: Metadata = {
  title: "Before & After Gallery - Elbey Projects Auto Repair",
  description: "See our work: before and after photos of brake repairs, engine service, suspension work, and more. Professional mobile mechanic results.",
};

const galleryItems = [
  {
    id: 1,
    type: "before-after",
    title: "Brake Pad Replacement - Honda Civic",
    before: "/images/brake-before.jpg",
    after: "/images/brake-after.jpg",
    description: "Complete brake service including pad replacement and rotor resurfacing. Customer reported much smoother stopping power.",
    category: "Brakes"
  },
  {
    id: 2,
    type: "video",
    title: "Engine Diagnostic Process",
    thumbnail: "/images/engine-diagnostic.jpg",
    videoUrl: "/videos/engine-diagnostic.mp4",
    description: "Real-time diagnostic scanning revealing a faulty oxygen sensor. Quick replacement restored proper fuel efficiency.",
    category: "Diagnostics"
  },
  {
    id: 3,
    type: "before-after",
    title: "Suspension Overhaul - Ford F-150",
    before: "/images/suspension-before.jpg",
    after: "/images/suspension-after.jpg",
    description: "Full suspension rebuild with new shocks, struts, and ball joints. Truck now rides like new.",
    category: "Suspension"
  },
  {
    id: 4,
    type: "before-after",
    title: "Oil Change & Filter Service",
    before: "/images/oil-before.jpg",
    after: "/images/oil-after.jpg",
    description: "Complete oil change with synthetic oil and premium filter. Engine runs quieter and more efficiently.",
    category: "Maintenance"
  },
  {
    id: 5,
    type: "video",
    title: "Mobile Repair - Emergency Brake Job",
    thumbnail: "/images/mobile-repair.jpg",
    videoUrl: "/videos/mobile-repair.mp4",
    description: "Emergency roadside brake repair. Customer was able to drive safely to our shop for complete service.",
    category: "Mobile Service"
  },
  {
    id: 6,
    type: "before-after",
    title: "Cooling System Service - Toyota Camry",
    before: "/images/cooling-before.jpg",
    after: "/images/cooling-after.jpg",
    description: "Radiator flush and coolant replacement. No more overheating issues, even in hot weather.",
    category: "Engine Service"
  }
];

const categories = ["All", "Brakes", "Diagnostics", "Suspension", "Maintenance", "Mobile Service", "Engine Service"];

export default function Gallery() {
  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Our Work
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            See the quality and craftsmanship in every repair
          </p>
        </div>
      </section>

      {/* Filter Categories */}
      <section className="py-8 bg-gray-900 border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-4">
            {categories.map((category) => (
              <button
                key={category}
                className="px-6 py-2 bg-gray-800 hover:bg-red-600 text-white rounded-full transition-colors"
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Gallery Grid */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {galleryItems.map((item) => (
              <div key={item.id} className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800 hover:border-red-600 transition-colors group cursor-pointer">
                {item.type === "before-after" ? (
                  <div className="relative">
                    <div className="grid grid-cols-2 gap-1">
                      <div className="aspect-square bg-gray-800 overflow-hidden relative">
                        <picture>
                          <source srcSet={`${item.before?.replace('.jpg','-256.webp')} 256w, ${item.before?.replace('.jpg','.webp')} 512w`} type="image/webp" />
                          <source srcSet={`${item.before?.replace('.jpg','.avif')} 512w`} type="image/avif" />
                          <img src={item.before} alt={`${item.title} before`} className="w-full h-full object-cover" loading="lazy" width={512} height={512} />
                        </picture>
                        <span className="text-gray-400 text-xs absolute top-2 left-2 bg-black/50 px-2 py-1 rounded">Before</span>
                      </div>
                      <div className="aspect-square bg-gray-800 overflow-hidden relative">
                        <picture>
                          <source srcSet={`${item.after?.replace('.jpg','-256.webp')} 256w, ${item.after?.replace('.jpg','.webp')} 512w`} type="image/webp" />
                          <source srcSet={`${item.after?.replace('.jpg','.avif')} 512w`} type="image/avif" />
                          <img src={item.after} alt={`${item.title} after`} className="w-full h-full object-cover" loading="lazy" width={512} height={512} />
                        </picture>
                        <span className="text-gray-400 text-xs absolute top-2 right-2 bg-black/50 px-2 py-1 rounded">After</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="relative aspect-video bg-gray-800 flex items-center justify-center group-hover:bg-gray-700 transition-colors">
                    <Play className="w-12 h-12 text-red-600 group-hover:scale-110 transition-transform" />
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-black/40 transition-colors" />
                    <span className="text-gray-400 text-xs absolute top-2 left-2 bg-black/50 px-2 py-1 rounded">Video</span>
                  </div>
                )}

                <div className="p-6">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                    <span className="text-xs bg-red-600 text-white px-2 py-1 rounded-full">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Ready to See Results Like These?</h2>
          <p className="text-gray-300 mb-8 text-lg">
            Professional auto repair services with guaranteed satisfaction
          </p>
          <a
            href="/#booking"
            className="inline-flex items-center px-8 py-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md transition-colors"
          >
            Book Your Service
          </a>
        </div>
      </section>
    </main>
  );
}
