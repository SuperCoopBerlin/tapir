import { Configuration } from "../api-client";
import { getCookie } from "../utils/getCookie";

export function useApi<T>(
  ApiClient: new (configuration: Configuration) => T,
): T {
  return new ApiClient(
    new Configuration({
      basePath: "http://localhost:8000",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    }),
  );
}
