import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { FileText, Sparkles } from "lucide-react";

// The markdown synthesiser is intentionally disabled for V1. When it's
// re-enabled, this page should load `audit.final_report` from Mongo and
// render it with <MarkdownRenderer />. Keeping the route as a placeholder
// so the sidebar link isn't broken.
export default function ReportPage() {
  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Full Report" },
        ]}
      />
      <div className="flex-1 p-4 md:p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold tracking-tight">Full Report</h2>
          <p className="text-muted-foreground">
            The LLM-authored narrative report
          </p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <div className="flex items-center gap-2 text-muted-foreground/60">
              <FileText className="h-10 w-10" />
              <Sparkles className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium">Coming soon</p>
            <p className="max-w-md text-xs text-muted-foreground">
              The narrative markdown report is disabled in V1 to keep audits
              lean. All the structured data already lives in the other tabs —
              Overview, Keywords, Competitors, and Action Items.
            </p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
