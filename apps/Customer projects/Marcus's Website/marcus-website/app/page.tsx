import Hero from "@/components/Hero";
import Services from "@/components/Services";
import WhyUs from "@/components/WhyUs";
import Gallery from "@/components/Gallery";
import Testimonials from "@/components/Testimonials";
import Contact from "@/components/Contact";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Hero />
      <WhyUs />
      <Services />
      <Gallery />
      <Testimonials />
      <Contact />
    </main>
  );
}
