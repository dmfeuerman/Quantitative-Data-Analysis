import axios from "axios";
import YahooFinance from "yahoo-finance2";

const yahooFinance = new YahooFinance();

const HEADERS = {
  headers: {
    "User-Agent": "Dylan Feuerman Dylan.M.Feuerman@gmail.com"
  }
};

export class ComprehensiveDataFetcher {
  constructor(ticker, options = {}) {
    this.ticker = ticker.toUpperCase();
    this.cik = null;
    this.companyData = {};
    this.options = {
      startDate: options.startDate || "2020-01-01",
      endDate: options.endDate || new Date().toISOString().split("T")[0],
      enableCache: options.enableCache ?? true,
      rateLimit: options.rateLimit ?? 100
    };
    this.cache = {};
  }

  // =============================
  // UTILITY
  // =============================
calculateQuantMetrics(financials, yahoo, risk) {
  if (!financials || !yahoo?.info) return {};

  const ratios = {};

  const getLatest = (metric) => {
    if (!financials[metric]) return null;
    const s = financials[metric].sort((a,b)=>new Date(b.end)-new Date(a.end));
    return s[0]?.val ?? null;
  };

  const revenue = getLatest("Revenue");
  const netIncome = getLatest("NetIncome");
  const assets = getLatest("Assets");
  const equity = getLatest("StockholdersEquity");
  const liabilities = getLatest("Liabilities");
  const currentAssets = getLatest("CurrentAssets");
  const currentLiabilities = getLatest("CurrentLiabilities");
  const longTermDebt = getLatest("LongTermDebt");
  const operatingCashFlow = getLatest("OperatingCashFlow");

  const marketCap = yahoo?.info?.price?.marketCap;
  const sharesOutstanding = yahoo?.info?.defaultKeyStatistics?.sharesOutstanding;
  const beta = yahoo?.info?.defaultKeyStatistics?.beta;
  const ev = yahoo?.info?.financialData?.enterpriseValue;
  const ebitda = yahoo?.info?.financialData?.ebitda;

  /* ---- Profitability ---- */
  if(revenue && netIncome) ratios.netMargin = (netIncome / revenue) * 100;
  if(assets && netIncome) ratios.roa = (netIncome / assets) * 100;
  if(equity && netIncome) ratios.roe = (netIncome / equity) * 100;

  /* ---- Leverage ---- */
  if(equity && longTermDebt) ratios.debtToEquity = longTermDebt / equity;

  /* ---- Liquidity ---- */
  if(currentAssets && currentLiabilities) {
    ratios.currentRatio = currentAssets / currentLiabilities;
    ratios.quickRatio = currentAssets / currentLiabilities;
  }

  /* ---- Valuation ---- */
  if(marketCap && netIncome) ratios.peRatio = marketCap / netIncome;
  if(marketCap && revenue) ratios.priceToSales = marketCap / revenue;
  if(marketCap && equity) ratios.priceToBook = marketCap / equity;
  if(ev && ebitda) ratios.evToEbitda = ev / ebitda;

  /* ---- Cash Flow ---- */
  if(operatingCashFlow && marketCap) ratios.fcfYield = (operatingCashFlow / marketCap) * 100;

  /* ---- Risk ---- */
  if(risk) {
    ratios.beta = beta;
    ratios.sharpeRatio = risk.sharpeRatio;
    ratios.maxDrawdown = risk.maxDrawdown;
    ratios.volatility = risk.annualizedVolatility;
    ratios.valueAtRisk = risk.valueAtRisk95;
  }

  return ratios;
}

  async rateLimitedRequest(fn) {
    const result = await fn();
    if (this.options.rateLimit > 0) {
      await new Promise(res => setTimeout(res, this.options.rateLimit));
    }
    return result;
  }

  getCacheKey(method,...args){
    return `${method}_${args.join("_")}`;
  }

  getFromCache(key){
    if(!this.options.enableCache) return null;
    return this.cache[key] || null;
  }

  setCache(key,value){
    if(this.options.enableCache) {
      this.cache[key] = value;
    }
  }

  // =============================
  // SEC DATA
  // =============================

  async getCIK() {
    const cacheKey = this.getCacheKey("getCIK",this.ticker);
    const cached = this.getFromCache(cacheKey);
    if(cached) return cached;

    const url = "https://www.sec.gov/files/company_tickers.json";
    const { data } = await axios.get(url, HEADERS);

    for(const key in data) {
      const item = data[key];
      if(item.ticker.toUpperCase() === this.ticker){
        this.cik = String(item.cik_str).padStart(10,"0");
        this.setCache(cacheKey,this.cik);
        return this.cik;
      }
    }

    throw new Error(`Ticker ${this.ticker} not found`);
  }

  async getSECFilings(){
    if(!this.cik) await this.getCIK();

    const cacheKey = this.getCacheKey("getSECFilings",this.cik);
    const cached = this.getFromCache(cacheKey);
    if(cached) return cached;

    const url = `https://data.sec.gov/submissions/CIK${this.cik}.json`;
    const { data } = await this.rateLimitedRequest(()=>axios.get(url,HEADERS));
    this.setCache(cacheKey,data);
    return data;
  }

  async getXBRLFacts(){
    if(!this.cik) await this.getCIK();

    const cacheKey = this.getCacheKey("getXBRLFacts",this.cik);
    const cached = this.getFromCache(cacheKey);
    if(cached) return cached;

    const url = `https://data.sec.gov/api/xbrl/companyfacts/CIK${this.cik}.json`;
    const { data } = await this.rateLimitedRequest(()=>axios.get(url,HEADERS));
    this.setCache(cacheKey,data);
    return data;
  }

  parseFinancialStatements(xbrl){
    const facts = xbrl?.facts?.["us-gaap"] || {};

    const tags = {
      Revenue: ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
      NetIncome: ["NetIncomeLoss"],
      Assets: ["Assets"],
      Liabilities: ["Liabilities"],
      StockholdersEquity: ["StockholdersEquity"],
      CurrentAssets: ["AssetsCurrent"],
      CurrentLiabilities: ["LiabilitiesCurrent"],
      OperatingCashFlow: ["NetCashProvidedByUsedInOperatingActivities"],
      CapEx: ["PaymentsToAcquirePropertyPlantAndEquipment"]
    };

    const output = {};

    for(const [key,tagList] of Object.entries(tags)){
      for(const tag of tagList){
        if(facts[tag]?.units?.USD){
          output[key] = facts[tag].units.USD;
          break;
        }
      }
    }

    return output;
  }

  // =============================
  // YAHOO FINANCE
  // =============================

  async fetchHistoricalData(symbol, start, end){
    return yahooFinance.historical(symbol,{
      period1:new Date(start),
      period2:new Date(end),
      interval:"1d"
    });
  }

  async getYahooFinanceData(){
    const info = await yahooFinance.quoteSummary(this.ticker, {
      modules: [
        "price",
        "summaryDetail",
        "defaultKeyStatistics",
        "financialData"
      ]
    });

    const history = await this.fetchHistoricalData(
      this.ticker,
      this.options.startDate,
      this.options.endDate
    );

    return { info, history };
  }

  // =============================
  // RISK METRICS
  // =============================

  calculateRiskMetrics(history){
    if(!history || history.length<2) return null;

    const prices = history.map(h=>h.close);
    const returns = [];

    for(let i=1;i<prices.length;i++){
      returns.push((prices[i]-prices[i-1])/prices[i-1]);
    }

    const mean = avg(returns);
    const vol = std(returns);

    let peak = prices[0];
    let maxDD = 0;

    for(let price of prices){
      if(price>peak) peak=price;
      const dd = (price-peak)/peak;
      maxDD = Math.min(maxDD,dd);
    }

    return {
      dailyVolatility: vol,
      annualizedVolatility: vol*Math.sqrt(252),
      sharpeRatio: mean/vol,
      maxDrawdown: maxDD,
      annualizedReturn: mean*252
    };
  }

  // =============================
  // BASE RATIOS
  // =============================

  calculateFinancialRatios(financials){
    const latest = (key)=>{
      const arr = financials[key];
      if(!arr) return null;
      arr.sort((a,b)=>new Date(b.end)-new Date(a.end));
      return arr[0]?.val;
    }

    const ratios = {};

    const revenue = latest("Revenue");
    const income = latest("NetIncome");
    const assets = latest("Assets");
    const equity = latest("StockholdersEquity");

    if(revenue && income){
      ratios.netMargin = (income/revenue)*100;
    }

    if(assets && income){
      ratios.roa = (income/assets)*100;
    }

    if(equity && income){
      ratios.roe = (income/equity)*100;
    }

    return ratios;
  }

  // =============================
  // ADVANCED FINANCIAL METRICS
  // =============================

  calculateAdvancedMetrics(financials, yfData, riskMetrics){
    const latest = (key)=>{
      const arr = financials[key];
      if(!arr) return null;
      arr.sort((a,b)=>new Date(b.end)-new Date(a.end));
      return arr[0]?.val;
    }

    const metrics = {};

    const revenue = latest("Revenue");
    const income = latest("NetIncome");
    const assets = latest("Assets");
    const equity = latest("StockholdersEquity");

    const marketCap = yfData?.info?.price?.marketCap || null;

    if(marketCap && income) {
      metrics.peRatio = marketCap / income;
    }

    if(marketCap && revenue) {
      metrics.priceToSales = marketCap / revenue;
    }

    if(riskMetrics){
      metrics.beta = riskMetrics.beta || null;
      metrics.volatility = riskMetrics.annualizedVolatility;
      metrics.maxDrawdown = riskMetrics.maxDrawdown;
      metrics.sharpeRatio = riskMetrics.sharpeRatio;
    }

    return metrics;
  }

  // =============================
  // MASTER FETCH
  // =============================

  async fetchAllData(){
    const filings = await this.getSECFilings();
    const xbrl = await this.getXBRLFacts();
    const yfData = await this.getYahooFinanceData();

    const financials = this.parseFinancialStatements(xbrl);
    const risk = this.calculateRiskMetrics(yfData.history);
    const baseRatios = this.calculateQuantMetrics(financials, yfData, riskMetrics);

    const advanced = this.calculateAdvancedMetrics(financials, yfData, risk);

    this.companyData = {
      ticker: this.ticker,
      cik: this.cik,
      fetchedAt: new Date().toISOString(),
      SEC_Company_Info: {
        name: filings.name,
        sicDescription: filings.sicDescription,
        fiscalYearEnd: filings.fiscalYearEnd
      },
      Financial_Statements: financials,
      Financial_Ratios: {...baseRatios, ...advanced},
      Yahoo_Finance: yfData,
      Risk_Metrics: risk
    };

    return this.companyData;
  }

  // =============================
  // SUMMARY
  // =============================

  getSummary(){
    return {
      company: this.companyData.SEC_Company_Info?.name,
      ticker: this.ticker,
      ratios: this.companyData.Financial_Ratios,
      risk: this.companyData.Risk_Metrics
    };
  }
}

/* ================= HELPER MATH ================= */

function avg(arr){
  return arr.reduce((a,b)=>a+b,0)/arr.length;
}

function std(arr){
  const m = avg(arr);
  const variance = arr.reduce((a,b)=>a+(b-m)**2,0)/arr.length;
  return Math.sqrt(variance);
}
