"use client";

import { Button } from "@/components/ui/Button";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center bg-black text-white pt-20">
      {/* Background overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/50 to-black/80" />

      <div className="relative z-10 text-center max-w-4xl mx-auto px-4">
        {/* Logo */}
        <div className="mb-8">
            <picture>
              <source srcSet="/images/elbeylogo-256.webp 256w, /images/elbeylogo.webp 512w" type="image/webp" />
              <source srcSet="/images/elbeylogo.avif 512w" type="image/avif" />
              <img
                src="/images/elbeylogo.jpg"
                srcSet="/images/elbeylogo-256.webp 256w, /images/elbeylogo.webp 512w"
                alt="Elbey Projects Logo"
                className="w-32 h-32 mx-auto"
                loading="lazy"
                width={128}
                height={128}
              />
            </picture>
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl font-bold mb-4 text-white">
          Elbey Projects
        </h1>
        <h2 className="text-xl md:text-2xl mb-6 text-gray-300">
          Honest mobile mechanics & engine service
        </h2>

        {/* Subhead */}
        <p className="text-lg md:text-xl mb-8 text-gray-400">
          Fast diagnostics • Mobile repairs • 15 years of hands-on experience
        </p>

        {/* CTA Button */}
        <Button
          size="lg"
          className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 text-lg font-semibold"
          onClick={() => {
            document.getElementById('booking')?.scrollIntoView({ behavior: 'smooth' });
          }}
        >
          Book Inspection
        </Button>
      </div>
    </section>
  );
}
