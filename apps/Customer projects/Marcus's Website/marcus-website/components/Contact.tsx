"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

export default function Contact() {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    email: "",
    service: "",
    preferredDate: "",
    preferredTime: "",
    address: "",
    vehicle: "",
    description: "",
    referral: "",
    consent: false
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitMessage("");

    try {
      // Simulate form submission (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 1000));

      // In a real application, you would send this data to your backend
      console.log("Form submitted:", formData);

      // Show success message
      setSubmitMessage("Thank you! Your service request has been submitted. We'll contact you within 2 hours.");

      // Clear form
      setFormData({
        name: "",
        phone: "",
        email: "",
        service: "",
        preferredDate: "",
        preferredTime: "",
        address: "",
        vehicle: "",
        description: "",
        referral: "",
        consent: false
      });
    } catch (error) {
      setSubmitMessage("Sorry, there was an error submitting your request. Please call us at (555) 123-4567.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  return (
    <section id="booking" className="py-16 bg-gray-900">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Book Your Service
          </h2>
          <p className="text-gray-300 text-lg">
            Get your vehicle diagnosed and repaired by experienced professionals
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-black rounded-lg p-8 border border-gray-800">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-white font-medium mb-2">
                Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                placeholder="Your full name"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-white font-medium mb-2">
                Phone *
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                required
                value={formData.phone}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                placeholder="(555) 123-4567"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-white font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="service" className="block text-white font-medium mb-2">
                Service Needed
              </label>
              <select
                id="service"
                name="service"
                value={formData.service}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-red-500"
              >
                <option value="">Select a service</option>
                <option value="brakes">Brake Service</option>
                <option value="oil-change">Oil Change</option>
                <option value="diagnostics">Diagnostics</option>
                <option value="suspension">Suspension Repair</option>
                <option value="engine">Engine Service</option>
                <option value="transmission">Transmission</option>
                <option value="mobile">Mobile Repair</option>
                <option value="inspection">Pre-purchase Inspection</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="preferredDate" className="block text-white font-medium mb-2">
                Preferred Date
              </label>
              <input
                type="date"
                id="preferredDate"
                name="preferredDate"
                value={formData.preferredDate}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label htmlFor="preferredTime" className="block text-white font-medium mb-2">
                Preferred Time
              </label>
              <select
                id="preferredTime"
                name="preferredTime"
                value={formData.preferredTime}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-red-500"
              >
                <option value="">Select time</option>
                <option value="morning">Morning (9AM - 12PM)</option>
                <option value="afternoon">Afternoon (12PM - 5PM)</option>
                <option value="evening">Evening (5PM - 8PM)</option>
              </select>
            </div>
          </div>

          <div className="mt-6">
            <label htmlFor="address" className="block text-white font-medium mb-2">
              Address
            </label>
            <input
              type="text"
              id="address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
              placeholder="Your address or pickup/dropoff location"
            />
          </div>

          <div className="mt-6">
            <label htmlFor="vehicle" className="block text-white font-medium mb-2">
              Vehicle Make/Model/Year
            </label>
            <input
              type="text"
              id="vehicle"
              name="vehicle"
              value={formData.vehicle}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
              placeholder="e.g. Honda Civic 2018"
            />
          </div>

          <div className="mt-6">
            <label htmlFor="description" className="block text-white font-medium mb-2">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-red-500"
              placeholder="Describe the issue or service needed..."
            />
          </div>

          <div className="mt-6">
            <label htmlFor="referral" className="block text-white font-medium mb-2">
              How did you hear about us?
            </label>
            <select
              id="referral"
              name="referral"
              value={formData.referral}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:border-red-500"
            >
              <option value="">Select option</option>
              <option value="google">Google Search</option>
              <option value="yelp">Yelp</option>
              <option value="facebook">Facebook</option>
              <option value="referral">Friend/Family Referral</option>
              <option value="repeat">Repeat Customer</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="mt-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="consent"
                checked={formData.consent}
                onChange={handleChange}
                required
                className="mr-3 w-4 h-4 text-red-600 bg-gray-800 border-gray-700 rounded focus:ring-red-500"
              />
              <span className="text-gray-300 text-sm">
                I agree to receive SMS/calls about my booking and service updates.
              </span>
            </label>
          </div>

          <div className="mt-8 text-center">
            <Button
              type="submit"
              size="lg"
              disabled={isSubmitting}
              className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white px-12 py-4 text-lg font-semibold"
            >
              {isSubmitting ? "Submitting..." : "Book Service Now"}
            </Button>
          </div>
        </form>

        {submitMessage && (
          <div className={`mt-6 p-4 rounded-lg text-center ${
            submitMessage.includes("error") || submitMessage.includes("Sorry")
              ? "bg-red-900/50 border border-red-700 text-red-200"
              : "bg-green-900/50 border border-green-700 text-green-200"
          }`}>
            {submitMessage}
          </div>
        )}

        <div className="mt-12 text-center">
          <div className="grid md:grid-cols-3 gap-6 text-gray-300">
            <div>
              <h3 className="font-semibold text-white mb-2">Call Us</h3>
              <p>(555) 123-4567</p>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-2">Email</h3>
              <p>service@elbeyprojects.com</p>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-2">Hours</h3>
              <p>24/7 Emergency Service</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
