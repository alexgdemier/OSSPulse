export function getApiBaseUrl() {
  const configuredUrl = process.env.OSSPULSE_API_URL;
  if (configuredUrl) return configuredUrl.replace(/\/$/, "");

  const boundServiceUrl = process.env.API_SERVICE_URL;
  if (boundServiceUrl) return `${boundServiceUrl.replace(/\/$/, "")}/api/v1`;

  return "http://127.0.0.1:8002/api/v1";
}
