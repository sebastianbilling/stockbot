import Decimal from "decimal.js";

export function formatCurrency(value: string | number): string {
  const d = new Decimal(value);
  return d.toFixed(2);
}

export function formatPercent(value: string | number): string {
  const d = new Decimal(value);
  const sign = d.isPositive() ? "+" : "";
  return `${sign}${d.toFixed(2)}%`;
}

export function calcPnL(quantity: string, costBasis: string, currentPrice: string) {
  const q = new Decimal(quantity);
  const cost = new Decimal(costBasis);
  const price = new Decimal(currentPrice);
  const totalCost = q.mul(cost);
  const totalValue = q.mul(price);
  const pnl = totalValue.minus(totalCost);
  const pnlPercent = totalCost.isZero()
    ? new Decimal(0)
    : pnl.div(totalCost).mul(100);

  return {
    totalCost: totalCost.toFixed(2),
    totalValue: totalValue.toFixed(2),
    pnl: pnl.toFixed(2),
    pnlPercent: pnlPercent.toFixed(2),
    isPositive: pnl.gte(0),
  };
}
