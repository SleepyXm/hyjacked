import { useState } from "react";
import { Trade } from "../types/charts";
import { PriceLineOptions } from "lightweight-charts";

export function PriceLines(
  seriesRef: React.MutableRefObject<any | null>,
  priceLinesRef: React.MutableRefObject<any[]>,
  trades: Trade[]
) {
  if (!seriesRef.current) return;

  // Remove existing lines
  priceLinesRef.current.forEach(line => {
    seriesRef.current.removePriceLine(line);
  });
  priceLinesRef.current = [];

  // Add new lines
  trades.forEach(trade => {
    if (typeof trade.entry_price !== 'number') return;

    const priceLineOptions: PriceLineOptions = {
      price: trade.entry_price,
      color: trade.action === 'buy' ? '#00FF8F' : '#FF3C3C',
      lineWidth: 2,
      lineStyle: 2,
      axisLabelVisible: true,
      axisLabelColor: 'black',
      axisLabelTextColor: 'white',
      lineVisible: true,
      title: `${trade.action.toUpperCase()} @ ${trade.entry_price.toFixed(2)}`,
    };

    const priceLine = seriesRef.current.createPriceLine(priceLineOptions);
    priceLinesRef.current.push(priceLine);
  });
}

export default function TradeButtonRow({data, ticker, activeTrades, setActiveTrades,}:
  {data: any; ticker: string; activeTrades: Trade[]; setActiveTrades: React.Dispatch<React.SetStateAction<Trade[]>>;}) 
  {
  const handleTrade = async (action: "buy" | "sell") => {
    const price = action === "buy" ? data.buy_price : data.close;
    if (typeof price !== "number") {
      alert("Invalid price data.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/trade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticker,
          action,
          price,
          buy_price: data.buy_price,
          sell_price: data.close,
          time: data.time,
        })
      });

      const result = await res.json();
      setActiveTrades((prev) => [...prev, result.data]);
      alert(
        `${action.toUpperCase()} order placed!\nPnL: $${result.data.pnl} | Spread: $${result.data.spread}`
      );
    } catch (e) {
      console.error(e);
    }
  };

  const handleCloseTrade = async (tradeId: number) => {
    try {
      await fetch(`http://localhost:8000/api/trade/${tradeId}`, {
        method: "DELETE"
      });
      setActiveTrades((prev) => prev.filter((t) => t.trade_id !== tradeId));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <div className="flex gap-4 mb-2 items-center">
        <button
          onClick={() => handleTrade("sell")}
          className="bg-red-400 text-white px-4 py-2 rounded flex flex-col items-center hover:bg-red-500 transition"
        >
          Sell
          <small>${typeof data.close === "number" ? data.close.toFixed(2) : "-"}</small>
        </button>

        <button
          onClick={() => handleTrade("buy")}
          className="bg-blue-400 text-white px-4 py-2 rounded flex flex-col items-center hover:bg-blue-500 transition"
        >
          Buy
          <small>${typeof data.buy_price === "number" ? data.buy_price.toFixed(2) : "-"}</small>
        </button>
      </div>

      {!!activeTrades.length && (
        <div className="bg-neutral-100 p-3 rounded shadow-md">
          <h3 className="font-semibold mb-2">Open Positions</h3>
          <ul className="space-y-2">
            {activeTrades.map((trade) => {
              const currentPrice = typeof data.close === "number" ? data.close : 0;
              const direction = trade.action === "buy" ? 1 : -1;
              const entry = trade.entry_price || 0;
              const livePnL = (currentPrice - entry) * direction;

              return (
                <li
                  key={trade.trade_id}
                  className="flex justify-between items-center bg-white p-2 rounded border"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {trade.action.toUpperCase()} {trade.ticker}
                    </p>
                    <p className="text-xs text-gray-600">
                      Entry: ${entry.toFixed(2)} | Current: ${currentPrice.toFixed(2)} | PnL:{" "}
                      <span className={livePnL >= 0 ? "text-green-600" : "text-red-600"}>
                        ${livePnL.toFixed(2)}
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => handleCloseTrade(trade.trade_id)}
                    className="text-sm text-red-500 hover:underline"
                  >
                    X
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </>
  );
}