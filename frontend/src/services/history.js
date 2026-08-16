const KEY = "jain-ai-history";

export function getHistory() {
  try {
    return (
      JSON.parse(
        localStorage.getItem(KEY),
      ) || []
    );
  } catch {
    return [];
  }
}

export function saveHistory(history) {
  localStorage.setItem(
    KEY,
    JSON.stringify(history),
  );
}

export function clearHistory() {
  localStorage.removeItem(KEY);
}
