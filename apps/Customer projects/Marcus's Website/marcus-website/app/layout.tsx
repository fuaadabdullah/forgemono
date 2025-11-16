import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import SpeedInsights from "@/components/SpeedInsights";
import "./globals.css";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Elbey Projects - Mobile Mechanic & Engine Service",
  description: "Professional mobile mechanic services in your area. Engine service, brakes, transmission, suspension, and diagnostics. 15 years of experience.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const GA_ID = process.env.NEXT_PUBLIC_GA_ID || process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS || "";
  const FB_PIXEL_ID = process.env.NEXT_PUBLIC_FB_PIXEL_ID || process.env.NEXT_PUBLIC_FACEBOOK_PIXEL || "";
  return (
    <html lang="en">
      <head>
        {GA_ID && (
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
            strategy="afterInteractive"
          />
        )}
        {GA_ID && (
          <Script id="google-analytics" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){window.dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${GA_ID}');
            `}
          </Script>
        )}
        {FB_PIXEL_ID && (
          <Script id="facebook-pixel" strategy="afterInteractive">
            {`
              !function(f,b,e,v,n,t,s)
              {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
              n.callMethod.apply(n,arguments):n.queue.push(arguments)};
              if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
              n.queue=[];t=b.createElement(e);t.async=!0;
              t.src=v;s=b.getElementsByTagName(e)[0];
              s.parentNode.insertBefore(t,s)}(window, document,'script',
              'https://connect.facebook.net/en_US/fbevents.js');
              fbq('init', '${FB_PIXEL_ID}');
              fbq('track', 'PageView');
            `}
          </Script>
        )}
      </head>
      <body className={inter.className}>
        <Navigation />
        {children}
        <Footer />
        {process.env.NEXT_PUBLIC_SITE_URL && <SpeedInsights />}
      </body>
    </html>
  );
}
