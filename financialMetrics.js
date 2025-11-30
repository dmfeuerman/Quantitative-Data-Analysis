export function buildExtendedRatios({Financial_Statements, Yahoo_Finance, Risk_Metrics}) {

  const is = Financial_Statements.incomeStatement;
  const bs = Financial_Statements.balanceSheet;
  const cf = Financial_Statements.cashFlow;

  const ratios = {};

  /* --- Income Statement --- */
  ratios.revenue = is.revenue;
  ratios.revenueGrowth = pctChange(is.revenue, is.prevRevenue);
  ratios.grossMargin = (is.grossProfit / is.revenue) * 100;
  ratios.operatingMargin = (is.operatingIncome / is.revenue) * 100;
  ratios.netMargin = (is.netIncome / is.revenue) * 100;
  ratios.ebitdaMargin = (is.ebitda / is.revenue) * 100;
  ratios.taxRate = (is.taxExpense / is.preTaxIncome) * 100;
  ratios.eps = is.netIncome / Yahoo_Finance.sharesOutstanding;

  /* --- Balance Sheet --- */
  ratios.bookValuePerShare = bs.totalEquity / Yahoo_Finance.sharesOutstanding;
  ratios.currentRatio = bs.currentAssets / bs.currentLiabilities;
  ratios.debtToEquity = bs.totalLiabilities / bs.totalEquity;

  /* --- Cash Flow --- */
  ratios.freeCashFlow = cf.operatingCashFlow - cf.capex;

  /* --- Profitability --- */
  ratios.roa = (is.netIncome / bs.totalAssets) * 100;
  ratios.roe = (is.netIncome / bs.totalEquity) * 100;
  ratios.roic = (is.netIncome / (bs.totalEquity + bs.totalDebt)) * 100;

  /* --- Valuation --- */
  ratios.peRatio = Yahoo_Finance.marketCap / is.netIncome;
  ratios.priceToSales = Yahoo_Finance.marketCap / is.revenue;
  ratios.priceToBook = Yahoo_Finance.marketCap / bs.totalEquity;
  ratios.fcfYield = (ratios.freeCashFlow / Yahoo_Finance.marketCap) * 100;

  /* --- Risk --- */
  ratios.beta = Yahoo_Finance.beta;
  ratios.volatility = stdDev(Risk_Metrics.dailyReturns);
  ratios.sharpeRatio = sharpe(Risk_Metrics.dailyReturns);
  ratios.maxDrawdown = maxDrawdown(Risk_Metrics.dailyReturns);

  return ratios;
}

/* ===== Helper Functions ===== */
function pctChange(current, previous){
  if(!previous) return null;
  return ((current - previous) / previous) * 100;
}

function stdDev(arr){
  const mean = arr.reduce((a,b)=>a+b) / arr.length;
  const variance = arr.reduce((a,b)=>a + (b-mean)**2 ,0) / arr.length;
  return Math.sqrt(variance);
}

function sharpe(returns){
  const mean = returns.reduce((a,b)=>a+b)/returns.length;
  const dev = stdDev(returns);
  return dev === 0 ? 0 : mean/dev;
}

function maxDrawdown(returns){
  let peak = 0;
  let maxDD = 0;
  let equity = 0;

  for(let r of returns){
    equity += r;
    peak = Math.max(peak, equity);
    maxDD = Math.min(maxDD, equity - peak);
  }
  return maxDD;
}
