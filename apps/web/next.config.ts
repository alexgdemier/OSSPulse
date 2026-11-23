import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const appRoot = fileURLToPath(new URL(".", import.meta.url));
const nextConfig: NextConfig = {
  ...(process.env.VERCEL === "1" ? {} : { output: "standalone" as const }),
  outputFileTracingRoot: appRoot,
};

export default nextConfig;
