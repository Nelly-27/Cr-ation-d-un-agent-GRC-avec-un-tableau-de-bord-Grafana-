import type { NextConfig } from "next";

// « standalone » : image Docker légère (seuls les fichiers nécessaires à l'exécution).
const nextConfig: NextConfig = { output: "standalone" };

export default nextConfig;
