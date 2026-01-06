import React, { useEffect, useMemo, useRef, useState } from "react";
import type { RaceControlApiResponse } from "../types";
import { AnimatePresence, motion } from "framer-motion";
import { RaceControlFlag } from "./RaceControlFlag";

type VRBuilderLivePreviewProps = {};

export function VRBuilderLivePreview({}: VRBuilderLivePreviewProps) {
  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-4 h-140 overflow-y-auto">
        <div className="pb-2 text-xs opacity-60 tracking-wide flex items-center">
          <span>Live Preview</span>
        </div>
      </div>
    </div>
  );
}
