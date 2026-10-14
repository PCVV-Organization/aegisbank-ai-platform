export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}
