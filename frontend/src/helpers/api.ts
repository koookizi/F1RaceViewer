/**
 * Fetches JSON data from an API endpoint with basic error handling.
 *
 * Attempts to parse the response as JSON, falling back to text if parsing
 * fails. Non-success responses are converted into a structured error
 * object for easier handling in the frontend.
 *
 * Args:
 *     url (string): API endpoint to request.
 *
 * Returns:
 *     Promise<T>: Parsed response data.
 */
export async function fetchJson<T>(url: string): Promise<T> {
    const res = await fetch(url);

    let body: any = null;

    try {
        body = await res.json();
    } catch {
        body = await res.text();
    }

    if (!res.ok) {
        throw {
            status: res.status,
            error: body?.error,
            message: body?.message || "Something went wrong",
        };
    }

    return body as T;
}
