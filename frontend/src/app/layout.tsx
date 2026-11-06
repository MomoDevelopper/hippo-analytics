import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "HIPPO ANALYTICS — PMU Burkina Faso",
  description: "Plateforme intelligente d'analyse et de prédiction hippique pour PMU Burkina Faso (LONAB)",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="bg-gray-50 font-sans antialiased">
        <Providers>
          <div className="flex h-screen overflow-hidden">
            {/* Sidebar de navigation */}
            <Sidebar />
            {/* Contenu principal */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-y-auto p-6">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
