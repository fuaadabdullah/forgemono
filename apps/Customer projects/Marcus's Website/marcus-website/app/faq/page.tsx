import { Metadata } from "next";
import FAQ from "@/components/FAQ";

export const metadata: Metadata = {
  title: "FAQ - Elbey Projects Mobile Mechanic",
  description: "Frequently asked questions about our mobile mechanic services, pricing, turnaround times, and service areas.",
};

export default function FAQPage() {
  return <FAQ />;
}
