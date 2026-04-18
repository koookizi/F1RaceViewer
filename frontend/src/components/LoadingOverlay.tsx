import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  loading: boolean;
  progress?: number;
  label?: string;
}

export function LoadingOverlay({
  loading,
  progress = 0,
  label = "Loading",
}: LoadingOverlayProps) {
  const safeProgress = Math.max(0, Math.min(100, progress));

  return (
    <AnimatePresence>
      {loading && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.96 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
          className="fixed bottom-6 left-1/2 z-100 w-[min(92vw,440px)] -translate-x-1/2"
        >
          <div className="overflow-hidden rounded-2xl border border-white/15 bg-neutral-900/80 shadow-2xl backdrop-blur-xl">
            <div className="px-5 py-4">
              <div className="mb-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 ring-1 ring-white/10">
                    <Loader2 className="h-5 w-5 animate-spin text-white/90" />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-white/75">Please wait, this can take a few minutes.</p>
                    <p className="text-base font-semibold tracking-tight text-white">
                      {label}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-2xl font-semibold tracking-tight text-white">
                    {Math.round(safeProgress)}%
                  </p>
                </div>
              </div>

              <div className="relative h-3 w-full overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full bg-white"
                  initial={{ width: 0 }}
                  animate={{ width: `${safeProgress}%` }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                />

                <motion.div
                  className="absolute inset-y-0 w-24 rounded-full bg-gradient-to-r from-transparent via-white/60 to-transparent"
                  animate={{ x: ["-120%", "520%"] }}
                  transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}