"use client";

import { Suspense } from "react";
import JobApplicationsPage from "../../../src/screens/admin/JobApplicationsPage";
import { Loader2 } from "lucide-react";

export default function AllApplications() {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center p-20"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div>}>
      <JobApplicationsPage />
    </Suspense>
  );
}
