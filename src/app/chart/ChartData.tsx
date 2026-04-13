import { useEffect, useState, useRef } from 'react';

const API_BASE = "http://localhost:8000/api"
const STOCK_DATA_URL = `${API_BASE}/stockdata?ticker_symbol=`;
const LIVE_DATA_URL = API_BASE.replace(/^http/, 'ws') + '/ws/stockdata';

export function useChartData<T extends { time: string } = any>(ticker: string, interval: string) {
  const [data, setData] = useState<T[] | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!ticker || !interval) return;

    const fetchData = async () => {
      try {
        const res = await fetch(`${STOCK_DATA_URL}${ticker}&interval=${interval}`);
        const data = await res.json();
        setData(data);
      } catch (err) {
        console.error("Nothing to see here:", err);
      }
    };

    fetchData();
  }, [ticker, interval]);

  useEffect(() => {
    if (!ticker || !interval) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    const socket = new WebSocket(`${LIVE_DATA_URL}?ticker_symbol=${encodeURIComponent(ticker)}&interval=${encodeURIComponent(interval)}`);
    wsRef.current = socket;

    socket.onmessage = (event) => {
      try {
        const latestCandle: T = JSON.parse(event.data);

        setData((currentData) => {
          if (!currentData || currentData.length === 0) return [latestCandle];

          const lastCandle = currentData[currentData.length - 1];

          if (lastCandle.time === latestCandle.time) {
            return [...currentData.slice(0, -1), latestCandle];
          } else if (lastCandle.time < latestCandle.time) {
            return [...currentData, latestCandle];
          }

          return currentData;
        });
      } catch (e) {
        console.error("Websocket message parse error:", e);
      }
    };

    socket.onerror = (error) => {
      console.error("Websocket error:", error);
    };

    socket.onclose = () => {
      console.log("Websocket closed");
    };

    return () => {
      socket.close();
      wsRef.current = null;
    };
  }, [ticker, interval]);

  return data;
}