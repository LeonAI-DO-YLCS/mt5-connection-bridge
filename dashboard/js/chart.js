export function drawCandles(canvas, prices) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#102338";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (!prices || prices.length === 0) {
    ctx.fillStyle = "#9eb7ce";
    ctx.fillText("No price data to chart.", 10, 20);
    return;
  }

  const highs = prices.map((p) => p.high);
  const lows = prices.map((p) => p.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const spread = max - min || 1;

  const candleWidth = Math.max(2, Math.floor((canvas.width - 40) / prices.length));

  prices.forEach((price, index) => {
    const x = 20 + index * candleWidth;
    const yHigh = 20 + ((max - price.high) / spread) * (canvas.height - 40);
    const yLow = 20 + ((max - price.low) / spread) * (canvas.height - 40);
    const yOpen = 20 + ((max - price.open) / spread) * (canvas.height - 40);
    const yClose = 20 + ((max - price.close) / spread) * (canvas.height - 40);
    const up = price.close >= price.open;

    ctx.strokeStyle = up ? "#58e6a9" : "#ff6b6b";
    ctx.beginPath();
    ctx.moveTo(x + candleWidth / 2, yHigh);
    ctx.lineTo(x + candleWidth / 2, yLow);
    ctx.stroke();

    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(1, Math.abs(yClose - yOpen));
    ctx.fillStyle = up ? "#58e6a9" : "#ff6b6b";
    ctx.fillRect(x, bodyTop, candleWidth - 1, bodyHeight);
  });
}
