import { Play } from "lucide-react";

const galleryItems = [
  {
    id: 1,
    type: "image",
    title: "Brake Pad Replacement",
    before: "/images/brake-before.jpg",
    after: "/images/brake-after.jpg"
  },
  {
    id: 2,
    type: "video",
    title: "Engine Diagnostics",
    thumbnail: "/images/engine-diagnostic.jpg",
    videoUrl: "/videos/engine-diagnostic.mp4"
  },
  {
    id: 3,
    type: "image",
    title: "Suspension Repair",
    before: "/images/suspension-before.jpg",
    after: "/images/suspension-after.jpg"
  }
];

export default function Gallery() {
  return (
    <section className="py-16 bg-gray-900">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-white">
          Our Work
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {galleryItems.map((item) => (
            <div key={item.id} className="bg-black rounded-lg overflow-hidden border border-gray-800">
              {(() => {
                if (item.type === 'image') {
                  const before = (item as any).before as string;
                  const after = (item as any).after as string;
                  return (
                    <div className="relative">
                      <div className="grid grid-cols-2 gap-1">
                        <div className="aspect-square bg-gray-800 overflow-hidden">
                          <picture>
                            <source srcSet={`${before.replace('.jpg','-256.webp')} 256w, ${before.replace('.jpg','.webp')} 512w`} type="image/webp" />
                            <source srcSet={`${before.replace('.jpg','.avif')} 512w`} type="image/avif" />
                            <img src={before} alt={`${item.title} before`} className="w-full h-full object-cover" loading="lazy" width={512} height={512} />
                          </picture>
                          <div className="absolute bottom-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">Before</div>
                        </div>
                        <div className="aspect-square bg-gray-800 overflow-hidden">
                          <picture>
                            <source srcSet={`${after.replace('.jpg','-256.webp')} 256w, ${after.replace('.jpg','.webp')} 512w`} type="image/webp" />
                            <source srcSet={`${after.replace('.jpg','.avif')} 512w`} type="image/avif" />
                            <img src={after} alt={`${item.title} after`} className="w-full h-full object-cover" loading="lazy" width={512} height={512} />
                          </picture>
                          <div className="absolute bottom-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">After</div>
                        </div>
                      </div>
                    </div>
                  );
                }
                return (
                <div className="relative aspect-video bg-gray-800 flex items-center justify-center group cursor-pointer">
                  <Play className="w-12 h-12 text-red-600 group-hover:scale-110 transition-transform" />
                  <div className="absolute inset-0 bg-black/20 group-hover:bg-black/40 transition-colors" />
                </div>
                )
              })()}

              <div className="p-4">
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-gray-300 text-sm">
                  Professional service with attention to detail
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <a
            href="/gallery"
            className="inline-flex items-center px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md transition-colors"
          >
            View Full Gallery
          </a>
        </div>
      </div>
    </section>
  );
}
