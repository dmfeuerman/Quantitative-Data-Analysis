import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import yfinance as yf
import time
from model import Model
from graph import FinancialVisualizer
from excel import EXCEL_WALKER
import shutil

HEADERS = {
    "User-Agent": "Dylan Feuerman Dylan.M.Feuerman@gmail.com"
}

class ComprehensiveDataFetcher:
    def __init__(self):
        self.viz = FinancialVisualizer()
        self.excel = EXCEL_WALKER()
        
    # =====================================
    # SEC DATA
    # =====================================
    def set_ticker(self, ticker):
        
        self.ticker = ticker.upper()
        self.clean_output_directory()
        self.cik = None  # Reset CIK when ticker changes
    def multi_ticker(self, debug_count=None):
        count = 0
        """Get CIK from ticker"""
        url = "https://www.sec.gov/files/company_tickers.json"
        data = requests.get(url, headers=HEADERS).json()
        for item in data.values():
            self.cik = str(item["cik_str"]).zfill(10)
            self.run_all(item["ticker"])
            print("hi")
            if debug_count:
                count += 1
                if count >= debug_count:
                    break
    def get_cik(self):
        """Get CIK from ticker"""
        url = "https://www.sec.gov/files/company_tickers.json"
        data = requests.get(url, headers=HEADERS).json()
        
        for item in data.values():
            if item["ticker"].upper() == self.ticker:
                self.cik = str(item["cik_str"]).zfill(10)
                return self.cik
        raise Exception(f"Ticker {self.ticker} not found in SEC database")
    
    def get_sec_filings(self):
        """Get all SEC filings data"""
        if not self.cik:
            self.get_cik()
            
        url = f"https://data.sec.gov/submissions/CIK{self.cik}.json"
        response = requests.get(url, headers=HEADERS)
        time.sleep(0.1)  # Rate limiting
        return response.json()
    
    def get_xbrl_facts(self):
        """Get XBRL financial facts"""
        if not self.cik:
            self.get_cik()
            
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"
        response = requests.get(url, headers=HEADERS)
        time.sleep(0.1)
        return response.json()
    
    def parse_financial_statements(self, xbrl):
        """Parse comprehensive financial statement data from XBRL"""
        facts = xbrl.get("facts", {}).get("us-gaap", {})
        
        # Income Statement Items
        income_statement = {
            "Revenue": "Revenues",
            "RevenueTotal": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "CostOfRevenue": "CostOfRevenue",
            "GrossProfit": "GrossProfit",
            "ResearchDevelopment": "ResearchAndDevelopmentExpense",
            "SellingGeneralAdmin": "SellingGeneralAndAdministrativeExpense",
            "OperatingExpenses": "OperatingExpenses",
            "OperatingIncome": "OperatingIncomeLoss",
            "InterestExpense": "InterestExpense",
            "TaxExpense": "IncomeTaxExpenseBenefit",
            "NetIncome": "NetIncomeLoss",
            "EPS_Basic": "EarningsPerShareBasic",
            "EPS_Diluted": "EarningsPerShareDiluted",
            "WeightedAverageShares": "WeightedAverageNumberOfSharesOutstandingBasic",
            "WeightedAverageSharesDiluted": "WeightedAverageNumberOfDilutedSharesOutstanding"
        }
        
        # Balance Sheet Items
        balance_sheet = {
            "Assets": "Assets",
            "CurrentAssets": "AssetsCurrent",
            "Cash": "CashAndCashEquivalentsAtCarryingValue",
            "ShortTermInvestments": "ShortTermInvestments",
            "AccountsReceivable": "AccountsReceivableNetCurrent",
            "Inventory": "InventoryNet",
            "PropertyPlantEquipment": "PropertyPlantAndEquipmentNet",
            "Goodwill": "Goodwill",
            "IntangibleAssets": "IntangibleAssetsNetExcludingGoodwill",
            "Liabilities": "Liabilities",
            "CurrentLiabilities": "LiabilitiesCurrent",
            "AccountsPayable": "AccountsPayableCurrent",
            "ShortTermDebt": "ShortTermBorrowings",
            "LongTermDebt": "LongTermDebt",
            "LongTermDebtCurrent": "LongTermDebtCurrent",
            "StockholdersEquity": "StockholdersEquity",
            "RetainedEarnings": "RetainedEarningsAccumulatedDeficit",
            "CommonStock": "CommonStockValue",
            "TreasuryStock": "TreasuryStockValue"
        }
        
        # Cash Flow Statement Items
        cash_flow = {
            "OperatingCashFlow": "NetCashProvidedByUsedInOperatingActivities",
            "InvestingCashFlow": "NetCashProvidedByUsedInInvestingActivities",
            "FinancingCashFlow": "NetCashProvidedByUsedInFinancingActivities",
            "CapEx": "PaymentsToAcquirePropertyPlantAndEquipment",
            "Depreciation": "DepreciationDepletionAndAmortization",
            "StockBasedComp": "ShareBasedCompensation",
            "DividendsPaid": "PaymentsOfDividends",
            "StockRepurchase": "PaymentsForRepurchaseOfCommonStock",
            "DebtIssuance": "ProceedsFromIssuanceOfLongTermDebt",
            "DebtRepayment": "RepaymentsOfLongTermDebt",
            "ChangeInWorkingCapital": "IncreaseDecreaseInOperatingCapital"
        }
        
        all_metrics = {**income_statement, **balance_sheet, **cash_flow}
        
        output = {}
        for name, tag in all_metrics.items():
            if tag in facts and "units" in facts[tag]:
                try:
                    df = pd.DataFrame(facts[tag]["units"].get("USD", []))
                    if not df.empty:
                        output[name] = df
                except:
                    pass
        
        return output
    
    def get_latest_10k_text(self, company_data):
        """Download and parse latest 10-K"""
        forms = company_data["filings"]["recent"]["form"]
        accessions = company_data["filings"]["recent"]["accessionNumber"]
        documents = company_data["filings"]["recent"]["primaryDocument"]
        
        for i, form in enumerate(forms):
            if form == "10-K":
                accession = accessions[i]
                document = documents[i]
                accession_clean = accession.replace("-", "")
                url = f"https://www.sec.gov/Archives/edgar/data/{int(self.cik)}/{accession_clean}/{document}"
                
                time.sleep(0.1)
                html = requests.get(url, headers=HEADERS).text
                soup = BeautifulSoup(html, "lxml")
                return soup.get_text("\n")
        
        return None
    
    # =====================================
    # YAHOO FINANCE DATA
    # =====================================
    
    def get_yfinance_data(self):
        """Get comprehensive data from Yahoo Finance"""
        stock = yf.Ticker(self.ticker)
        
        data = {
            "info": stock.info,
            "history": stock.history(period="max"),
            "financials": stock.financials,
            "quarterly_financials": stock.quarterly_financials,
            "balance_sheet": stock.balance_sheet,
            "quarterly_balance_sheet": stock.quarterly_balance_sheet,
            "cashflow": stock.cashflow,
            "quarterly_cashflow": stock.quarterly_cashflow,
            "earnings_dates": stock.earnings_dates,
            "shares": stock.get_shares_full(start="2010-01-01"),
            "actions": stock.actions,  # Dividends and splits
            "institutional_holders": stock.institutional_holders,
            "major_holders": stock.major_holders,
            "insider_transactions": stock.insider_transactions,
            "insider_roster": stock.insider_roster_holders,
            "recommendations": stock.recommendations,
            "analyst_price_targets": stock.analyst_price_targets,
            "earnings_estimate": stock.earnings_estimate,
            "revenue_estimate": stock.revenue_estimate,
            "earnings_history": stock.earnings_history,
            "upgrades_downgrades": stock.upgrades_downgrades
        }
        
        return data
    
    # =====================================
    # CALCULATIONS
    # =====================================
    
    def calculate_financial_ratios(self, financials, yf_data):
        """Calculate comprehensive financial ratios"""
        ratios = {}
        
        try:
            # Get latest values from SEC data
            rev = financials.get("Revenue", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "Revenue" in financials else None
            net = financials.get("NetIncome", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "NetIncome" in financials else None
            assets = financials.get("Assets", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "Assets" in financials else None
            equity = financials.get("StockholdersEquity", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "StockholdersEquity" in financials else None
            liab = financials.get("Liabilities", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "Liabilities" in financials else None
            current_assets = financials.get("CurrentAssets", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "CurrentAssets" in financials else None
            current_liab = financials.get("CurrentLiabilities", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "CurrentLiabilities" in financials else None
            lt_debt = financials.get("LongTermDebt", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "LongTermDebt" in financials else None
            ocf = financials.get("OperatingCashFlow", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "OperatingCashFlow" in financials else None
            capex = financials.get("CapEx", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "CapEx" in financials else None
            op_income = financials.get("OperatingIncome", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "OperatingIncome" in financials else None
            interest = financials.get("InterestExpense", pd.DataFrame()).get("val", pd.Series()).iloc[-1] if "InterestExpense" in financials else None
            
            # Profitability Ratios
            if rev and net:
                ratios["Net_Profit_Margin"] = net / rev
            if rev and op_income:
                ratios["Operating_Margin"] = op_income / rev
            if assets and net:
                ratios["ROA"] = net / assets
            if equity and net and equity > 0:
                ratios["ROE"] = net / equity
            
            # Liquidity Ratios
            if current_assets and current_liab and current_liab > 0:
                ratios["Current_Ratio"] = current_assets / current_liab
            
            # Leverage Ratios
            if liab and assets and assets > 0:
                ratios["Debt_Ratio"] = liab / assets
            if lt_debt and equity and equity > 0:
                ratios["Debt_to_Equity"] = lt_debt / equity
            if op_income and interest and interest > 0:
                ratios["Interest_Coverage"] = op_income / abs(interest)
            
            # Cash Flow Ratios
            if ocf and capex:
                ratios["Free_Cash_Flow"] = ocf - abs(capex)
            
            # Market ratios from YF
            info = yf_data.get("info", {})
            ratios["PE_Ratio"] = info.get("trailingPE")
            ratios["Forward_PE"] = info.get("forwardPE")
            ratios["PEG_Ratio"] = info.get("pegRatio")
            ratios["Price_to_Book"] = info.get("priceToBook")
            ratios["Price_to_Sales"] = info.get("priceToSalesTrailing12Months")
            ratios["EV_to_Revenue"] = info.get("enterpriseToRevenue")
            ratios["EV_to_EBITDA"] = info.get("enterpriseToEbitda")
            ratios["Dividend_Yield"] = info.get("dividendYield")
            ratios["Beta"] = info.get("beta")
            
        except Exception as e:
            print(f"Error calculating ratios: {e}")
        
        return ratios
    
    def calculate_growth_metrics(self, financials):
        """Calculate growth rates"""
        growth = {}
        
        try:
            for metric in ["Revenue", "NetIncome", "OperatingCashFlow"]:
                if metric in financials:
                    df = financials[metric]
                    if "val" in df.columns and len(df) > 1:
                        df_sorted = df.sort_values("end")
                        values = df_sorted["val"].values
                        
                        if len(values) >= 2:
                            yoy = (values[-1] - values[-2]) / abs(values[-2]) if values[-2] != 0 else None
                            growth[f"{metric}_YoY_Growth"] = yoy
                        
                        if len(values) >= 5:
                            cagr_5y = (values[-1] / values[-5]) ** (1/5) - 1 if values[-5] > 0 else None
                            growth[f"{metric}_CAGR_5Y"] = cagr_5y
        except Exception as e:
            print(f"Error calculating growth: {e}")
        
        return growth
    
    def calculate_risk_metrics(self, yf_data):
        """Calculate risk and volatility metrics"""
        risk = {}
        
        try:
            history = yf_data["history"]
            if not history.empty and "Close" in history.columns:
                returns = history["Close"].pct_change().dropna()
                
                # Volatility
                risk["Volatility_Daily"] = returns.std()
                risk["Volatility_Annualized"] = returns.std() * np.sqrt(252)
                
                # Sharpe Ratio (assuming 4% risk-free rate)
                risk_free = 0.04 / 252
                excess_returns = returns - risk_free
                if excess_returns.std() > 0:
                    risk["Sharpe_Ratio"] = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
                
                # Downside deviation for Sortino
                downside = returns[returns < 0]
                if len(downside) > 0 and downside.std() > 0:
                    risk["Sortino_Ratio"] = (excess_returns.mean() / downside.std()) * np.sqrt(252)
                
                # Maximum drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                risk["Max_Drawdown"] = drawdown.min()
                
                # VaR (95% confidence)
                risk["VaR_95"] = returns.quantile(0.05)
                
        except Exception as e:
            print(f"Error calculating risk metrics: {e}")
        
        return risk
    
    # =====================================
    # MAIN ORCHESTRATION
    # =====================================
    
    def fetch_all_data(self):
        """Fetch all available data"""
        print(f"\n{'='*60}")
        print(f"Fetching comprehensive data for {self.ticker}")
        print(f"{'='*60}\n")
        
        all_data = {}
        
        # 1. SEC Data
        print("📄 Fetching SEC filings...")
        try:
            sec_data = self.get_sec_filings()
            all_data["SEC_Company_Info"] = sec_data
            print("   ✓ SEC company info fetched")
        except Exception as e:
            print(f"   ✗ SEC data error: {e}")
            sec_data = {}
        
        # 2. XBRL Financial Data
        print("📊 Fetching XBRL financial data...")
        try:
            xbrl = self.get_xbrl_facts()
            all_data["XBRL_Raw"] = xbrl
            financials = self.parse_financial_statements(xbrl)
            all_data["Financial_Statements"] = financials
            print(f"   ✓ Parsed {len(financials)} financial metrics")
        except Exception as e:
            print(f"   ✗ XBRL error: {e}")
            financials = {}
        
        # 3. Yahoo Finance Data
        print("💹 Fetching Yahoo Finance data...")
        try:
            yf_data = self.get_yfinance_data()
            all_data["Yahoo_Finance"] = yf_data
            print("   ✓ Yahoo Finance data fetched")
        except Exception as e:
            print(f"   ✗ Yahoo Finance error: {e}")
            yf_data = {}
        
        # 4. Calculated Metrics
        print("🧮 Calculating derived metrics...")
        try:
            ratios = self.calculate_financial_ratios(financials, yf_data)
            all_data["Financial_Ratios"] = ratios
            print(f"   ✓ Calculated {len(ratios)} ratios")
        except Exception as e:
            print(f"   ✗ Ratio calculation error: {e}")
        
        try:
            growth = self.calculate_growth_metrics(financials)
            all_data["Growth_Metrics"] = growth
            print(f"   ✓ Calculated {len(growth)} growth metrics")
        except Exception as e:
            print(f"   ✗ Growth calculation error: {e}")
        
        try:
            risk = self.calculate_risk_metrics(yf_data)
            all_data["Risk_Metrics"] = risk
            print(f"   ✓ Calculated {len(risk)} risk metrics")
        except Exception as e:
            print(f"   ✗ Risk calculation error: {e}")
        
        # 5. Latest 10-K text
        print("📑 Fetching latest 10-K text...")
        try:
            if sec_data:
                text_10k = self.get_latest_10k_text(sec_data)
                all_data["Latest_10K_Text"] = text_10k
                print("   ✓ 10-K text fetched")
        except Exception as e:
            print(f"   ✗ 10-K fetch error: {e}")
        
        self.company_data = all_data
        return all_data
    
    # =====================================
    # SAVE DATA
    # =====================================
    
    def save_all_data(self, output_dir=None):
        """Save all data to organized folder structure"""
        if not output_dir:
            output_dir = f"{self.ticker}_COMPLETE_DATA"
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving data to {output_dir}...")
        
        # 1. Save raw JSON data
        json_dir = os.path.join(output_dir, "01_Raw_JSON")
        os.makedirs(json_dir, exist_ok=True)
        
        for key in ["SEC_Company_Info", "XBRL_Raw", "Yahoo_Finance"]:
            if key in self.company_data:
                try:
                    # Handle non-serializable objects
                    data_to_save = self._make_serializable(self.company_data[key])
                    with open(f"{json_dir}/{key}.json", "w") as f:
                        json.dump(data_to_save, f, indent=2, default=str)
                except Exception as e:
                    print(f"   ⚠ Could not save {key}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 2. Save financial statements as CSV
        csv_dir = os.path.join(output_dir, "02_Financial_Statements")
        os.makedirs(csv_dir, exist_ok=True)
        
        if "Financial_Statements" in self.company_data:
            for name, df in self.company_data["Financial_Statements"].items():
                try:
                    df.to_csv(f"{csv_dir}/{name}.csv", index=False)
                except Exception as e:
                    print(f"   ⚠ Could not save {name}: {e}")
        
        # 3. Save calculated metrics
        metrics_dir = os.path.join(output_dir, "03_Calculated_Metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        for key in ["Financial_Ratios", "Growth_Metrics", "Risk_Metrics"]:
            if key in self.company_data:
                try:
                    data_to_save = self._make_serializable(self.company_data[key])
                    with open(f"{metrics_dir}/{key}.json", "w") as f:
                        json.dump(data_to_save, f, indent=2, default=str)
                except Exception as e:
                    print(f"   ⚠ Could not save {key}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 4. Save historical price data
        if "Yahoo_Finance" in self.company_data and "history" in self.company_data["Yahoo_Finance"]:
            history_dir = os.path.join(output_dir, "04_Market_Data")
            os.makedirs(history_dir, exist_ok=True)
            
            try:
                self.company_data["Yahoo_Finance"]["history"].to_csv(
                    f"{history_dir}/Price_History.csv"
                )
            except:
                pass
        
        # 5. Save 10-K text
        if "Latest_10K_Text" in self.company_data:
            text_dir = os.path.join(output_dir, "05_Filing_Text")
            os.makedirs(text_dir, exist_ok=True)
            
            with open(f"{text_dir}/Latest_10K.txt", "w", encoding="utf-8") as f:
                f.write(self.company_data["Latest_10K_Text"])
        
        # 6. Create summary report
        self._create_summary_report(output_dir)
        
        print(f"✅ All data saved successfully to {output_dir}\n")
        
    
    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif isinstance(obj, dict):
            return {str(k): self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif pd.isna(obj):
            return None
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return obj
    
    def _create_summary_report(self, output_dir):
        """Create a human-readable summary report"""
        report_path = os.path.join(output_dir, "SUMMARY_REPORT.txt")
        
        with open(report_path, "w") as f:
            f.write(f"{'='*80}\n")
            f.write(f"COMPREHENSIVE DATA REPORT FOR {self.ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            
            # Company info
            if "Yahoo_Finance" in self.company_data:
                info = self.company_data["Yahoo_Finance"].get("info", {})
                f.write(f"Company Name: {info.get('longName', 'N/A')}\n")
                f.write(f"Sector: {info.get('sector', 'N/A')}\n")
                f.write(f"Industry: {info.get('industry', 'N/A')}\n")
                f.write(f"Market Cap: ${info.get('marketCap', 0):,.0f}\n\n")
            
            # Financial Ratios
            if "Financial_Ratios" in self.company_data:
                f.write("KEY FINANCIAL RATIOS\n")
                f.write("-" * 80 + "\n")
                for key, value in self.company_data["Financial_Ratios"].items():
                    if value is not None:
                        f.write(f"{key}: {value:.4f}\n")
                f.write("\n")
            
            # Growth Metrics
            if "Growth_Metrics" in self.company_data:
                f.write("GROWTH METRICS\n")
                f.write("-" * 80 + "\n")
                for key, value in self.company_data["Growth_Metrics"].items():
                    if value is not None:
                        f.write(f"{key}: {value:.2%}\n")
                f.write("\n")
            
            # Risk Metrics
            if "Risk_Metrics" in self.company_data:
                f.write("RISK METRICS\n")
                f.write("-" * 80 + "\n")
                for key, value in self.company_data["Risk_Metrics"].items():
                    if value is not None:
                        f.write(f"{key}: {value:.4f}\n")
                f.write("\n")
            
            f.write(f"{'='*80}\n")
            f.write("Data Sources:\n")
            f.write("- SEC EDGAR (financial statements, filings)\n")
            f.write("- Yahoo Finance (market data, analyst estimates)\n")
            f.write(f"{'='*80}\n")
    def clean_output_directory(self, output_dir=None):
        """Remove existing output directory to start fresh"""
        if not output_dir:
            output_dir = f"{self.ticker}_COMPLETE_DATA"
        
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
            print(f"🧹 Cleaned existing directory: {output_dir}")
        else:
            print(f"No existing directory to clean: {output_dir}")
        if not os.path.isdir("stock_data"):
            os.mkdir("stock_data")
        if not os.path.isdir(f"stock_data/{self.ticker}"):
            os.mkdir(f"stock_data/{self.ticker}")
            os.mkdir(f"stock_data/{self.ticker}/charts")
    
    def run_all(self, ticker):
        self.set_ticker(ticker)
        self.fetch_all_data()
        self.save_all_data()
        self.viz.set_data_dir(ticker)
        self.viz.run_all()
        
        self.excel.set_path(ticker)
        self.excel.walk()
        
        self.remove_non_used_data()
    
    def remove_non_used_data(self):

        shutil.copyfile(f"{self.ticker}_COMPLETE_DATA/SUMMARY_REPORT.txt", f"stock_data/{self.ticker}/SUMMARY_REPORT.txt")
        shutil.rmtree(f"{self.ticker}_COMPLETE_DATA")
    

# =====================================
# USAGE
# =====================================

if __name__ == "__main__":
    tickers = ["A", "IE"]  # Change this to any ticker
    #Model(ticker).run_all()
    fetcher = ComprehensiveDataFetcher()
    #fetcher.run_all(tickers[0])
    fetcher.multi_ticker(debug_count=5)
        
