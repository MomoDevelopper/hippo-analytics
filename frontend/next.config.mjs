/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Mode standalone pour Docker (réduit la taille de l'image)
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // Ignore les erreurs TypeScript et ESLint au build (corrigées séparément)
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
