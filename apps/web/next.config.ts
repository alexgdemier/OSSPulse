import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const appRoot = fileURLToPath(new URL(".", import.meta.url));
const nextConfig: NextConfig = { output: "standalone", outputFileTracingRoot: appRoot };

export default nextConfig;
