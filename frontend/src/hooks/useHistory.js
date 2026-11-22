import { useState, useEffect } from "react";

const API = "http://localhost:8000/api";

export function useHistory() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetch_ = () =>
      fetch(`${API}/history?limit=20`)
        .then((r) => r.json())
        .then((data) => {
          const formatted = data.reverse().map((h) => ({
            time: new Date(h.timestamp * 1000).toLocaleTimeString(),
            occupied: h.occupied,
            free: h.free,
          }));
          setHistory(formatted);
        })
        .catch(() => {});

    fetch_();
    const id = setInterval(fetch_, 10000);
    return () => clearInterval(id);
  }, []);

  return history;
}
