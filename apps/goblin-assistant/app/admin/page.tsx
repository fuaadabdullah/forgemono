import { Metadata } from "next";
import { AdminOverview } from "./components/admin-overview";

export const metadata: Metadata = {
  title: "Admin Dashboard - Goblin Assistant",
  description: "System monitoring and operations dashboard",
};

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Overview</h1>
        <p className="text-gray-600 mt-2">
          Monitor system health, provider status, and performance metrics
        </p>
      </div>
      
      <AdminOverview />
    </div>
  );
}
