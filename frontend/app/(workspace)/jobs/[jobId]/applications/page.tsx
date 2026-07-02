import JobApplicationsPage from "../../../../../src/screens/admin/JobApplicationsPage";

export default function Page({ params }: { params: { jobId: string } }) {
  return <JobApplicationsPage jobId={params.jobId} />;
}
