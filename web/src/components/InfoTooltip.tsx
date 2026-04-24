import * as Tooltip from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";

interface Props {
  content: ReactNode;
  children?: ReactNode;
}

/** Hover-/keyboard-accessible tooltip used next to every form input. */
export function InfoTooltip({ content, children }: Props) {
  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          {children ?? (
            <button
              type="button"
              aria-label="More information"
              className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-slate-400 text-xs text-slate-600 hover:bg-slate-200 focus:ring-2 focus:ring-rclea-500"
            >
              ?
            </button>
          )}
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side="top"
            align="center"
            sideOffset={6}
            className="max-w-sm rounded-md bg-slate-900 px-3 py-2 text-sm leading-relaxed text-slate-100 shadow-lg animate-in fade-in-0 zoom-in-95"
          >
            {content}
            <Tooltip.Arrow className="fill-slate-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
