import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useState } from "react";
import { getDisclaimer } from "../pyodide/api";

interface Props {
  open: boolean;
  onAcknowledge: () => void;
  /** When true (from the sticky banner click), the button is optional — the user can just close it. */
  informational?: boolean;
  onClose?: () => void;
}

export function DisclaimerModal({ open, onAcknowledge, informational, onClose }: Props) {
  const [body, setBody] = useState<string>("Loading…");
  useEffect(() => {
    if (!open) return;
    getDisclaimer().then((d) => setBody(d.full)).catch((e) => setBody(String(e)));
  }, [open]);
  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-lg bg-white p-6 shadow-xl">
          <Dialog.Title className="text-xl font-bold text-rclea-900">
            RCLEA — educational use only
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-slate-600">
            Please read before using the tool.
          </Dialog.Description>
          <pre className="mt-4 max-h-64 overflow-y-auto whitespace-pre-wrap rounded bg-slate-50 p-4 text-xs text-slate-700">
            {body}
          </pre>
          <div className="mt-5 flex justify-end gap-3">
            {informational && (
              <button
                type="button"
                onClick={onClose}
                className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
              >
                Close
              </button>
            )}
            {!informational && (
              <button
                type="button"
                onClick={onAcknowledge}
                className="rounded bg-rclea-700 px-4 py-2 text-sm font-medium text-white hover:bg-rclea-900"
              >
                I understand — proceed
              </button>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
