import { Metadata } from "next";
import { notFound } from "next/navigation";
import { Calendar, Clock, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface BlogPost {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: string;
  image: string;
  content: string;
  slug: string;
  metaDescription: string;
}

const blogPosts: BlogPost[] = [
  {
    id: 1,
    title: "How to Tell If Your Suspension is Shot",
    excerpt: "Learn the warning signs of suspension problems and why addressing them early saves you money and ensures safety.",
    date: "2025-11-15",
    readTime: "5 min read",
    category: "Maintenance",
    image: "/images/suspension-blog.jpg",
    slug: "suspension-warning-signs",
    metaDescription: "Learn the warning signs of suspension problems and why addressing them early saves you money and ensures safety. Expert advice from Elbey Projects mobile mechanics.",
    content: `
# How to Tell If Your Suspension is Shot

Your vehicle's suspension system is crucial for safety, comfort, and handling. When it fails, it can lead to dangerous driving conditions and expensive damage. Here's how to spot the warning signs before they become major problems.

## Common Suspension Warning Signs

### 1. Uneven Tire Wear
If your tires are wearing unevenly, especially on the edges, it's often a sign of suspension issues. The suspension keeps your tires in proper contact with the road.

### 2. Vehicle Pulling to One Side
If your car pulls to the left or right while driving on a straight road, worn suspension components could be the culprit.

### 3. Bouncing or Excessive Body Roll
When you hit a bump, does your vehicle continue bouncing? Or does it roll excessively in corners? These are classic signs of worn shocks or struts.

### 4. Nose Diving During Braking
If your vehicle dips significantly forward when braking, your front suspension components may need attention.

### 5. Unusual Noises
Listen for clunking, knocking, or squeaking sounds when driving over bumps. These often indicate worn bushings or ball joints.

## Why Early Detection Matters

Ignoring suspension problems can lead to:
- Reduced braking effectiveness
- Poor handling and stability
- Increased tire wear and replacement costs
- Damage to other vehicle components
- Safety hazards, especially in emergency situations

## What We Check During Suspension Service

At Elbey Projects, our suspension inspections include:
- Visual inspection of all components
- Checking for leaks and damage
- Measuring ride height and alignment
- Testing shock absorber performance
- Inspecting bushings, ball joints, and control arms

## Prevention Tips

- Have your suspension checked annually
- Avoid potholes when possible
- Don't overload your vehicle
- Address issues promptly when noticed

Don't wait for suspension problems to become dangerous. Contact us for a thorough inspection and keep your vehicle safe and comfortable.
    `
  },
  {
    id: 2,
    title: "What a Pre-Purchase Inspection Covers",
    excerpt: "Complete guide to what our mechanics check during a vehicle pre-purchase inspection to protect your investment.",
    date: "2025-11-10",
    readTime: "7 min read",
    category: "Buying",
    image: "/images/inspection-blog.jpg",
    slug: "pre-purchase-inspection-guide",
    metaDescription: "Complete guide to what mechanics check during a vehicle pre-purchase inspection. Protect your investment with our comprehensive inspection service.",
    content: `
# What a Pre-Purchase Inspection Covers

Buying a used vehicle is a significant investment, and a pre-purchase inspection can save you thousands in unexpected repairs. Here's what our comprehensive inspection covers.

## Engine and Mechanical Systems

### Engine Performance
- Compression testing
- Oil pressure and condition
- Cooling system integrity
- Exhaust system inspection
- Timing belt/chain condition

### Transmission
- Fluid level and condition
- Shifting performance
- Clutch operation (manual transmissions)
- Differential and driveline components

## Electrical and Electronics

- Battery condition and charging system
- Starting system functionality
- All lights and signals
- Dashboard warning lights
- Infotainment and accessory systems

## Braking System

- Brake pad and rotor condition
- Brake fluid quality
- Brake lines and hoses
- Parking brake functionality
- ABS system operation

## Suspension and Steering

- Shock absorber performance
- Control arm and bushing condition
- Ball joint wear
- Wheel bearing operation
- Steering gear and linkage

## Tires and Wheels

- Tread depth and wear patterns
- Tire pressure and condition
- Wheel alignment
- Spare tire availability

## Body and Interior

- Frame and structural integrity
- Rust and corrosion
- Paint condition
- Interior components
- Seat belts and airbags

## Documentation Review

- Service history verification
- Accident history check
- Warranty status
- Recall information

## Our Inspection Process

1. **Visual Inspection**: Comprehensive exterior and interior examination
2. **Test Drive**: Performance evaluation under various conditions
3. **Diagnostic Scan**: Computer system analysis for hidden issues
4. **Under-Vehicle Inspection**: Critical components check
5. **Detailed Report**: Written findings with repair estimates

## Why Choose Our Pre-Purchase Inspection?

- Certified mechanics with 15+ years experience
- Mobile service - we come to you
- Detailed written report with photos
- Repair cost estimates
- Peace of mind guarantee

Don't buy a vehicle without knowing its true condition. Our pre-purchase inspection gives you the information you need to make an informed decision.
    `
  },
  {
    id: 3,
    title: "The Truth About Brake Pad Replacement",
    excerpt: "When to replace brake pads, what to expect during service, and why quality matters for your safety.",
    date: "2025-11-05",
    readTime: "4 min read",
    category: "Safety",
    image: "/images/brakes-blog.jpg",
    slug: "brake-pad-replacement-guide",
    metaDescription: "When to replace brake pads, what to expect during service, and why quality matters for your safety. Expert brake service from Elbey Projects.",
    content: `
# The Truth About Brake Pad Replacement

Your brakes are your vehicle's most important safety system. Understanding when and why to replace brake pads can save lives and money. Here's what you need to know.

## When to Replace Brake Pads

### Warning Signs
- Squealing or grinding noises when braking
- Reduced braking performance
- Vibration in the brake pedal
- Dashboard brake warning light
- Longer stopping distances

### Recommended Intervals
- Every 30,000-50,000 miles for most vehicles
- More frequently in heavy traffic or mountainous areas
- Immediately if warning signs appear

## What Happens During Brake Service

### Inspection Process
- Visual inspection of all brake components
- Measurement of pad thickness
- Rotor condition assessment
- Brake fluid quality check

### Replacement Procedure
- Removal of wheels and calipers
- Installation of new pads and hardware
- Rotor resurfacing or replacement if needed
- Brake fluid flush and bleed
- Test drive and adjustment

## Why Quality Matters

### Premium vs. Economy Pads
- **Ceramic Pads**: Quiet operation, less dust, better performance
- **Semi-Metallic Pads**: Good performance, moderate noise and dust
- **Organic Pads**: Budget option, more noise and dust

### OEM vs. Aftermarket
- OEM pads meet manufacturer specifications
- Quality aftermarket pads can match OEM performance
- Always choose pads rated for your vehicle

## Brake Rotor Considerations

### When Rotors Need Attention
- Deep scoring or grooves
- Warping from heat
- Minimum thickness reached
- Pulsing brake pedal

### Resurfacing vs. Replacement
- Resurfacing saves money when possible
- Replacement required for severely damaged rotors
- New rotors often included with premium pad kits

## Safety First

Your brakes are not something to skimp on. Quality brake service ensures:
- Reliable stopping power
- Predictable performance
- Reduced risk of accidents
- Extended rotor life

## Our Brake Service Promise

- Premium ceramic brake pads
- Lifetime warranty on workmanship
- 12-month/12,000-mile warranty on parts
- Safety inspection included
- Competitive pricing

Don't compromise on safety. Choose quality brake service you can trust.
    `
  },
  {
    id: 4,
    title: "Mobile Mechanic vs. Shop Service: Pros and Cons",
    excerpt: "Understanding the benefits of mobile repair services and when traditional shop service might be better.",
    date: "2025-10-30",
    readTime: "6 min read",
    category: "Service",
    image: "/images/mobile-blog.jpg",
    slug: "mobile-vs-shop-service",
    metaDescription: "Mobile mechanic vs. shop service: Understanding the benefits of mobile repair services and when traditional shop service might be better.",
    content: `
# Mobile Mechanic vs. Shop Service: Pros and Cons

Choosing between mobile mechanic service and traditional shop service depends on your needs, schedule, and the type of repair required. Here's a comprehensive comparison to help you decide.

## Mobile Mechanic Service Advantages

### Convenience
- **Come to You**: No need to drop off your vehicle
- **Flexible Scheduling**: Service at your home, office, or anywhere convenient
- **No Towing Required**: Saves time and money for minor repairs
- **Minimal Disruption**: Continue your day while we work

### Cost Effectiveness
- **Lower Overhead**: No shop rent or facility costs
- **Transparent Pricing**: Clear quotes with no hidden fees
- **Faster Service**: Often completed in one visit

### Personal Service
- **Dedicated Attention**: One mechanic handles your vehicle
- **Direct Communication**: Work directly with the technician
- **Trust Building**: Build relationship with your mechanic

## Traditional Shop Service Advantages

### Specialized Equipment
- **Heavy Equipment**: For major engine work or transmission service
- **Advanced Diagnostics**: Specialized tools for complex issues
- **Parts Inventory**: Immediate access to parts and supplies

### Comprehensive Facilities
- **Climate Control**: Consistent working environment
- **Multiple Bays**: Handle multiple vehicles simultaneously
- **Waiting Areas**: Comfortable space for customers

### Warranty and Insurance
- **Extended Warranties**: Better coverage options
- **Insurance Work**: Preferred by insurance companies
- **ASCs (Auto Service Contracts)**: Warranty company approved

## When to Choose Mobile Service

### Ideal For:
- Oil changes and routine maintenance
- Brake pad replacement
- Battery replacement
- Minor electrical repairs
- Emergency roadside service
- Diagnostic work

### Best When:
- You're short on time
- You have mobility challenges
- You need service outside business hours
- The repair is straightforward

## When to Choose Shop Service

### Necessary For:
- Major engine repairs
- Transmission work
- Suspension overhauls
- Body work or painting
- Extensive electrical system repairs

### Better When:
- Multiple issues need addressing
- Specialized equipment required
- Warranty work
- Insurance claims involved

## Our Mobile Service Approach

At Elbey Projects, we combine the best of both worlds:
- **Mobile Capability**: We come to you for most repairs
- **Shop Backup**: Access to shop facilities when needed
- **Quality Assurance**: Same standards regardless of location
- **Emergency Response**: 24/7 availability for breakdowns

## Making the Right Choice

Consider these factors when deciding:
- **Urgency**: How quickly do you need the service?
- **Complexity**: How involved is the repair?
- **Location**: Where is your vehicle located?
- **Budget**: What's your service budget?
- **Convenience**: How much disruption can you tolerate?

## The Hybrid Solution

Many customers benefit from both approaches:
- **Mobile for Maintenance**: Regular service at your location
- **Shop for Major Work**: Complex repairs in a controlled environment

Contact us to discuss your specific needs. We'll recommend the best service approach for your situation and vehicle.
    `
  }
];

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = blogPosts.find(p => p.slug === slug);

  if (!post) {
    return {
      title: "Blog Post Not Found",
    };
  }

  // Build absolute URLs for images if a SITE URL is provided in env
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_VERCEL_URL || '';
  const defaultImage = '/images/elbeylogo-256.webp';
  const imagePath = post.image || defaultImage;
  const absoluteImage = siteUrl ? `${siteUrl.replace(/\/$/, '')}${imagePath}` : imagePath;

  return {
    title: `${post.title} - Elbey Projects Blog`,
    description: post.metaDescription,
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      type: "article",
      publishedTime: post.date,
      images: [
        {
          url: absoluteImage,
          alt: post.title,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.title,
      description: post.metaDescription,
      images: [absoluteImage],
    },
  };
}

export async function generateStaticParams() {
  return blogPosts.map((post) => ({
    slug: post.slug,
  }));
}

export default async function BlogPost({ params }: PageProps) {
  const { slug } = await params;
  const post = blogPosts.find(p => p.slug === slug);

  if (!post) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto px-4">
          <Link
            href="/blog"
            className="inline-flex items-center text-red-400 hover:text-red-300 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Link>

          <div className="flex items-center space-x-4 mb-4">
            <span className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
              {post.category}
            </span>
            <div className="flex items-center text-gray-400 text-sm">
              <Calendar className="w-4 h-4 mr-1" />
              {new Date(post.date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
            <div className="flex items-center text-gray-400 text-sm">
              <Clock className="w-4 h-4 mr-1" />
              {post.readTime}
            </div>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            {post.title}
          </h1>

          {post.image && (
            <div className="max-w-2xl mx-auto mb-6">
              <picture>
                <source srcSet={`${post.image.replace('.jpg','-256.webp')} 256w, ${post.image.replace('.jpg','.webp')} 512w`} type="image/webp" />
                <source srcSet={`${post.image.replace('.jpg','.avif')} 512w`} type="image/avif" />
                <img src={post.image} alt={post.title} className="w-full h-auto rounded-lg object-cover" loading="lazy" />
              </picture>
            </div>
          )}
          <p className="text-xl text-gray-300">
            {post.excerpt}
          </p>
        </div>
      </section>

      {/* Content Section */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4">
          <article className="prose prose-lg prose-invert max-w-none">
            <div
              className="text-gray-300 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: post.content.replace(/\n/g, '<br />').replace(/^# (.+)$/gm, '<h2 class="text-2xl font-bold text-white mt-8 mb-4">$1</h2>').replace(/^## (.+)$/gm, '<h3 class="text-xl font-semibold text-white mt-6 mb-3">$1</h3>').replace(/^### (.+)$/gm, '<h4 class="text-lg font-medium text-white mt-4 mb-2">$1</h4>')
              }}
            />
          </article>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Need Auto Repair Service?</h2>
          <p className="text-gray-300 mb-8 text-lg">
            Get expert mobile mechanic service for your vehicle. Fast, reliable, and convenient.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/#booking"
              className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Book Service Now
            </Link>
            <a
              href="tel:+15551234567"
              className="bg-gray-800 hover:bg-gray-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Call (555) 123-4567
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
