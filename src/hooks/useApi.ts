import { Configuration } from "../api-client";
import { getCookie } from "../utils/getCookie";
import env from "../env.ts";

export function useApi<T>(
  ApiClient: new (configuration: Configuration) => T,
): T {
  return new ApiClient(
    new Configuration({
      basePath: env.REACT_APP_API_ROOT,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    }),
  );
}
