import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // export a fully static site so it can be served by FastAPI
  output: "export",
};

export default nextConfig;
