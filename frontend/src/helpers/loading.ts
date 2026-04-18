/**
 * Tracks asynchronous loading requests and calculates overall progress.
 *
 * Maintains a set of active request IDs alongside a running total of all
 * started requests. This allows components to determine whether loading
 * is in progress, how many requests remain pending, how many have
 * completed, and the percentage progress across all tracked requests.
 *
 * Each request should be started with a unique ID using 'startLoading'
 * and removed with 'stopLoading' once finished.
 *
 * Returns:
 *     Object:
 *         startLoading(id: string): Registers a request as active.
 *         stopLoading(id: string): Removes a completed request.
 *         resetProgress(): Resets the total request counter.
 *         isLoading (boolean): True when one or more requests are active.
 *         pendingCount (number): Number of active requests.
 *         completedCount (number): Number of completed requests.
 *         totalRequests (number): Total requests started.
 *         progress (number): Completion percentage (0–100).
 *         pendingIds (string[]): List of active request IDs.
 */
import { useCallback, useMemo, useState } from "react";

export function useLoadingTracker() {
    const [pendingRequests, setPendingRequests] = useState<Set<string>>(new Set());
    const [totalRequests, setTotalRequests] = useState(0);

    const startLoading = useCallback((id: string) => {
        setPendingRequests((prev) => {
            const next = new Set(prev);
            next.add(id);
            return next;
        });

        setTotalRequests((prev) => prev + 1);
    }, []);

    const stopLoading = useCallback((id: string) => {
        setPendingRequests((prev) => {
            const next = new Set(prev);
            next.delete(id);
            return next;
        });
    }, []);

    const pendingCount = pendingRequests.size;
    const completedCount = totalRequests - pendingCount;

    const progress =
        totalRequests === 0
            ? 0
            : Math.round((completedCount / totalRequests) * 100);

    const isLoading = pendingCount > 0;

    const resetProgress = useCallback(() => {
        setTotalRequests(0);
    }, []);

    const pendingIds = useMemo(() => Array.from(pendingRequests), [pendingRequests]);

    return {
        startLoading,
        stopLoading,
        resetProgress,
        isLoading,
        pendingCount,
        completedCount,
        totalRequests,
        progress,
        pendingIds,
    };
}