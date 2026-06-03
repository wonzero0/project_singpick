import { useEffect, useState } from "react";

const FAILURE_KEY = "singpick_login_failures";
const LOCKOUT_KEY = "singpick_login_lockout_until";
const MAX_FAILURES = 5;
const LOCKOUT_DURATION_SECONDS = 60;

function getNumberFromStorage(key: string, fallback = 0) {
  const raw = localStorage.getItem(key);
  return raw ? Number(raw) || fallback : fallback;
}

function setNumberInStorage(key: string, value: number) {
  localStorage.setItem(key, value.toString());
}

function clearLockoutStorage() {
  localStorage.removeItem(FAILURE_KEY);
  localStorage.removeItem(LOCKOUT_KEY);
}

export function useLoginLockout() {
  const [failureCount, setFailureCount] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [isLocked, setIsLocked] = useState(false);

  useEffect(() => {
    const updateState = () => {
      const lockUntil = getNumberFromStorage(LOCKOUT_KEY, 0);
      const now = Date.now();
      const locked = lockUntil > now;
      setIsLocked(locked);
      setRemainingSeconds(locked ? Math.max(0, Math.ceil((lockUntil - now) / 1000)) : 0);
      setFailureCount(getNumberFromStorage(FAILURE_KEY, 0));

      if (!locked) {
        clearLockoutStorage();
      }
    };

    updateState();
    const interval = window.setInterval(updateState, 1000);
    return () => window.clearInterval(interval);
  }, []);

  const recordFailure = () => {
    const currentCount = getNumberFromStorage(FAILURE_KEY, 0) + 1;
    setFailureCount(currentCount);
    setNumberInStorage(FAILURE_KEY, currentCount);

    if (currentCount >= MAX_FAILURES) {
      const lockUntil = Date.now() + LOCKOUT_DURATION_SECONDS * 1000;
      setNumberInStorage(LOCKOUT_KEY, lockUntil);
      setIsLocked(true);
      setRemainingSeconds(LOCKOUT_DURATION_SECONDS);
    }
  };

  const resetLockout = () => {
    clearLockoutStorage();
    setFailureCount(0);
    setIsLocked(false);
    setRemainingSeconds(0);
  };

  return {
    failureCount,
    isLocked,
    remainingSeconds,
    recordFailure,
    resetLockout,
  };
}
