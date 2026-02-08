import { Metadata } from "next";
import Link from "next/link";
import { Calendar, Clock } from "lucide-react";

export const metadata: Metadata = {
  title: "Blog - Auto Repair Tips & Maintenance Advice",
  description: "Expert auto repair advice, maintenance tips, and industry insights from Elbey Projects. Learn how to keep your vehicle running smoothly.",
};

const blogPosts = [
  {
    id: 1,
    title: "How to Tell If Your Suspension is Shot",
    excerpt: "Learn the warning signs of suspension problems and why addressing them early saves you money and ensures safety.",
    date: "2025-11-15",
    readTime: "5 min read",
    category: "Maintenance",
    image: "/images/suspension-blog.jpg",
    slug: "suspension-warning-signs"
  },
  {
    id: 2,
    title: "What a Pre-Purchase Inspection Covers",
    excerpt: "Complete guide to what our mechanics check during a vehicle pre-purchase inspection to protect your investment.",
    date: "2025-11-10",
    readTime: "7 min read",
    category: "Buying",
    image: "/images/inspection-blog.jpg",
    slug: "pre-purchase-inspection-guide"
  },
  {
    id: 3,
    title: "The Truth About Brake Pad Replacement",
    excerpt: "When to replace brake pads, what to expect during service, and why quality matters for your safety.",
    date: "2025-11-05",
    readTime: "4 min read",
    category: "Safety",
    image: "/images/brakes-blog.jpg",
    slug: "brake-pad-replacement-guide"
  },
  {
    id: 4,
    title: "Mobile Mechanic vs. Shop Service: Pros and Cons",
    excerpt: "Understanding the benefits of mobile repair services and when traditional shop service might be better.",
    date: "2025-10-30",
    readTime: "6 min read",
    category: "Service",
    image: "/images/mobile-blog.jpg",
    slug: "mobile-vs-shop-service"
  }
];

export default function Blog() {
  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Auto Repair Blog
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Expert advice to keep your vehicle running smoothly
          </p>
        </div>
      </section>

      {/* Blog Posts */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-8">
            {blogPosts.map((post) => (
              <article key={post.id} className="bg-gray-900 rounded-lg overflow-hidden border border-gray-800 hover:border-red-600 transition-colors">
                {/* Post Image */}
                <div className="h-48 bg-gray-800 flex items-center justify-center overflow-hidden">
                  <picture>
                    <source srcSet={`${post.image?.replace('.jpg','-256.webp')} 256w, ${post.image?.replace('.jpg','.webp')} 512w`} type="image/webp" />
                    <source srcSet={`${post.image?.replace('.jpg','.avif')} 512w`} type="image/avif" />
                    <img src={post.image} alt={post.title} className="w-full h-full object-cover" loading="lazy" width={720} height={320} />
                  </picture>
                </div>

                <div className="p-6">
                  <div className="flex items-center gap-4 mb-3">
                    <span className="text-xs bg-red-600 text-white px-2 py-1 rounded-full">
                      {post.category}
                    </span>
                    <div className="flex items-center text-gray-400 text-sm">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(post.date).toLocaleDateString()}
                    </div>
                    <div className="flex items-center text-gray-400 text-sm">
                      <Clock className="w-4 h-4 mr-1" />
                      {post.readTime}
                    </div>
                  </div>

                  <Link href={`/blog/${post.slug}`}>
                    <h2 className="text-xl font-semibold mb-3 text-white hover:text-red-400 transition-colors cursor-pointer">
                      {post.title}
                    </h2>
                  </Link>

                  <p className="text-gray-300 mb-4">{post.excerpt}</p>

                  <Link
                    href={`/blog/${post.slug}`}
                    className="text-red-400 hover:text-red-300 font-medium"
                  >
                    Read More →
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter Signup */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Stay Informed</h2>
          <p className="text-gray-300 mb-8 text-lg">
            Get the latest auto repair tips and maintenance advice delivered to your inbox.
          </p>

          <div className="max-w-md mx-auto">
            <form className="flex gap-4">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-black border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-md transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}
