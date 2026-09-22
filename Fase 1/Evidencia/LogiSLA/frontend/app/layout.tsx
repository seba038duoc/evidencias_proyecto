import type { Metadata } from "next";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "LogiSLA",
  description: "Auditoría inteligente de SLA de transporte",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">
        <SiteHeader />
        <div className="page-shell flex flex-1 flex-col">{children}</div>
      </body>
    </html>
  );
}
