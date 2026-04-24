import { useState } from "react";

export function DisclaimerBanner({ onShowFull }: { onShowFull: () => void }) {
  return (
    <div
      className="sticky top-0 z-40 border-b border-yellow-300 bg-yellow-50 px-4 py-2 text-sm text-yellow-900"
      role="complementary"
      aria-label="Disclaimer"
    >
      <strong className="mr-2">Educational use only.</strong>
      Not a regulatory tool. Author(s) accept no liability.
      <button
        type="button"
        onClick={onShowFull}
        className="ml-3 underline hover:text-yellow-700"
      >
        Read the full disclaimer
      </button>
    </div>
  );
}

const ACK_KEY = "rclea:disclaimer:acknowledged:v1";

export function useDisclaimerGate() {
  const [shown, setShown] = useState<boolean>(() => {
    try {
      return localStorage.getItem(ACK_KEY) === "yes";
    } catch {
      return false;
    }
  });
  const acknowledge = () => {
    try {
      localStorage.setItem(ACK_KEY, "yes");
    } catch {
      /* ignore */
    }
    setShown(true);
  };
  return { acknowledged: shown, acknowledge };
}
