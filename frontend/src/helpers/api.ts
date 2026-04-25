export class ApiError extends Error {
    status: number;
    error?: string;
    body?: unknown;

    constructor(message: string, status: number, error?: string, body?: unknown) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.error = error;
        this.body = body;
    }
}

/**
 * Fetches JSON data from an API endpoint with basic error handling.
 *
 * Successful responses return the parsed body. Non-success responses throw
 * an `ApiError` so callers can safely read `err.message` and `err.error`.
 */
export async function fetchJson<T>(url: string): Promise<T> {
    let res: Response;

    try {
        res = await fetch(url);
    } catch (error) {
        const message =
            error instanceof Error ? error.message : "Network request failed";
        throw new ApiError(message, 0, message);
    }

    let body: unknown = null;
    const contentType = res.headers.get("content-type") ?? "";

    if (res.status !== 204) {
        if (contentType.includes("application/json")) {
            try {
                body = await res.json();
            } catch {
                body = null;
            }
        } else {
            try {
                body = await res.text();
            } catch {
                body = null;
            }
        }
    }

    if (!res.ok) {
        const error =
            body &&
            typeof body === "object" &&
            "error" in body &&
            typeof body.error === "string"
                ? body.error
                : undefined;

        const message =
            body &&
            typeof body === "object" &&
            "message" in body &&
            typeof body.message === "string"
                ? body.message
                : typeof body === "string" && body.trim().length > 0
                  ? body
                  : error || `Request failed with status ${res.status}`;

        throw new ApiError(message, res.status, error, body);
    }

    return body as T;
}
