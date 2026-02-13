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
