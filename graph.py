import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class FinancialVisualizer:
    def __init__(self):
        pass
    def set_data_dir(self, ticker, data_dir=None):
        self.ticker = ticker.upper()
        self.data_dir = data_dir if data_dir else f"{ticker}_COMPLETE_DATA"
        self.figures = []
        
    def load_data(self):
        """Load all saved data"""
        print(f"Loading data for {self.ticker}...")
        
        # Load financial statements
        csv_dir = os.path.join(self.data_dir, "02_Financial_Statements")
        self.financials = {}
        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    name = file.replace('.csv', '')
                    self.financials[name] = pd.read_csv(os.path.join(csv_dir, file))
        
        # Load metrics
        metrics_dir = os.path.join(self.data_dir, "03_Calculated_Metrics")
        with open(os.path.join(metrics_dir, "Financial_Ratios.json")) as f:
            self.ratios = json.load(f)
        with open(os.path.join(metrics_dir, "Growth_Metrics.json")) as f:
            self.growth = json.load(f)
        with open(os.path.join(metrics_dir, "Risk_Metrics.json")) as f:
            self.risk = json.load(f)
        
        # Load market data
        market_dir = os.path.join(self.data_dir, "04_Market_Data")
        self.price_history = pd.read_csv(os.path.join(market_dir, "Price_History.csv"))
        self.price_history['Date'] = pd.to_datetime(self.price_history['Date'])
        
        print("✓ Data loaded successfully\n")
    
    def plot_revenue_and_income(self):
        """Plot Revenue and Net Income over time"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Revenue
        if "Revenue" in self.financials:
            df = self.financials["Revenue"].copy()
            df['end'] = pd.to_datetime(df['end'])
            df = df.sort_values('end')
            df = df[df['form'] == '10-K']  # Annual only
            
            ax1.plot(df['end'], df['val'] / 1e9, marker='o', linewidth=2, markersize=8)
            ax1.set_title(f'{self.ticker} - Annual Revenue', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Revenue (Billions $)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Add growth rate annotations
            if len(df) > 1:
                for i in range(1, len(df)):
                    growth = (df['val'].iloc[i] - df['val'].iloc[i-1]) / df['val'].iloc[i-1] * 100
                    ax1.annotate(f'{growth:+.1f}%', 
                                xy=(df['end'].iloc[i], df['val'].iloc[i] / 1e9),
                                xytext=(10, 10), textcoords='offset points',
                                fontsize=9, color='green' if growth > 0 else 'red')
        
        # Net Income
        if "NetIncome" in self.financials:
            df = self.financials["NetIncome"].copy()
            df['end'] = pd.to_datetime(df['end'])
            df = df.sort_values('end')
            df = df[df['form'] == '10-K']
            
            ax2.plot(df['end'], df['val'] / 1e9, marker='o', linewidth=2, 
                    markersize=8, color='green')
            ax2.set_title(f'{self.ticker} - Annual Net Income', fontsize=16, fontweight='bold')
            ax2.set_ylabel('Net Income (Billions $)', fontsize=12)
            ax2.set_xlabel('Year', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        self.figures.append(('revenue_income', fig))
        return fig
    
    def plot_balance_sheet(self):
        """Plot Assets, Liabilities, and Equity"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        data_to_plot = {}
        for metric in ["Assets", "Liabilities", "StockholdersEquity"]:
            if metric in self.financials:
                df = self.financials[metric].copy()
                df['end'] = pd.to_datetime(df['end'])
                df = df.sort_values('end')
                df = df[df['form'] == '10-K']
                data_to_plot[metric] = df
        
        if data_to_plot:
            for name, df in data_to_plot.items():
                label = name.replace('Stockholders', 'Shareholders ')
                ax.plot(df['end'], df['val'] / 1e9, marker='o', linewidth=2, 
                       markersize=8, label=label)
            
            ax.set_title(f'{self.ticker} - Balance Sheet Overview', fontsize=16, fontweight='bold')
            ax.set_ylabel('Amount (Billions $)', fontsize=12)
            ax.set_xlabel('Year', fontsize=12)
            ax.legend(fontsize=11, loc='best')
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        self.figures.append(('balance_sheet', fig))
        return fig
    
    def plot_cash_flows(self):
        """Plot Operating, Investing, and Financing Cash Flows"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        cash_metrics = {
            "OperatingCashFlow": "Operating",
            "InvestingCashFlow": "Investing", 
            "FinancingCashFlow": "Financing"
        }
        
        for metric, label in cash_metrics.items():
            if metric in self.financials:
                df = self.financials[metric].copy()
                df['end'] = pd.to_datetime(df['end'])
                df = df.sort_values('end')
                df = df[df['form'] == '10-K']
                
                ax.plot(df['end'], df['val'] / 1e9, marker='o', linewidth=2,
                       markersize=8, label=label)
        
        ax.set_title(f'{self.ticker} - Cash Flow Statement', fontsize=16, fontweight='bold')
        ax.set_ylabel('Cash Flow (Billions $)', fontsize=12)
        ax.set_xlabel('Year', fontsize=12)
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        self.figures.append(('cash_flows', fig))
        return fig
    
    def plot_profitability_ratios(self):
        """Plot key profitability ratios"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        ratios_to_plot = {
            'Net_Profit_Margin': 'Net Profit Margin',
            'Operating_Margin': 'Operating Margin',
            'ROA': 'Return on Assets (ROA)',
            'ROE': 'Return on Equity (ROE)'
        }
        
        for idx, (key, title) in enumerate(ratios_to_plot.items()):
            ax = axes[idx // 2, idx % 2]
            
            if key in self.ratios and self.ratios[key] is not None:
                value = self.ratios[key] * 100  # Convert to percentage
                colors = ['green' if value > 0 else 'red']
                ax.bar([title], [value], color=colors, alpha=0.7)
                ax.set_ylabel('Percentage (%)', fontsize=11)
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add value label on bar
                ax.text(0, value, f'{value:.2f}%', ha='center', 
                       va='bottom' if value > 0 else 'top', fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'Data Not Available', ha='center', va='center',
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(title, fontsize=12, fontweight='bold')
        
        plt.suptitle(f'{self.ticker} - Profitability Ratios', fontsize=16, fontweight='bold', y=1.00)
        plt.tight_layout()
        self.figures.append(('profitability_ratios', fig))
        return fig
    
    def plot_financial_ratios_dashboard(self):
        """Dashboard of various financial ratios"""
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes = axes.flatten()
        
        ratio_list = [
            ('Current_Ratio', 'Current Ratio', False),
            ('Debt_to_Equity', 'Debt-to-Equity', False),
            ('Interest_Coverage', 'Interest Coverage', False),
            ('PE_Ratio', 'P/E Ratio', False),
            ('Price_to_Book', 'Price-to-Book', False),
            ('Dividend_Yield', 'Dividend Yield', True)
        ]
        
        for idx, (key, title, is_percent) in enumerate(ratio_list):
            ax = axes[idx]
            
            if key in self.ratios and self.ratios[key] is not None:
                value = self.ratios[key]
                if is_percent:
                    value = value * 100
                
                color = 'steelblue'
                ax.bar([title], [value], color=color, alpha=0.7)
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')
                
                label = f'{value:.2f}%' if is_percent else f'{value:.2f}'
                ax.text(0, value, label, ha='center', 
                       va='bottom' if value > 0 else 'top', fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(title, fontsize=12, fontweight='bold')
        
        plt.suptitle(f'{self.ticker} - Financial Ratios Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        self.figures.append(('ratios_dashboard', fig))
        return fig
    
    def plot_stock_price(self):
        """Plot historical stock price with volume"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        df = self.price_history.copy()
        
        # Price chart
        ax1.plot(df['Date'], df['Close'], linewidth=1.5, label='Close Price')
        ax1.fill_between(df['Date'], df['Low'], df['High'], alpha=0.2, label='Daily Range')
        ax1.set_title(f'{self.ticker} - Stock Price History', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Add moving averages
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        ax1.plot(df['Date'], df['MA50'], linewidth=1, alpha=0.7, label='50-day MA', linestyle='--')
        ax1.plot(df['Date'], df['MA200'], linewidth=1, alpha=0.7, label='200-day MA', linestyle='--')
        ax1.legend(loc='best')
        
        # Volume chart
        colors = ['green' if close >= open_ else 'red' 
                 for close, open_ in zip(df['Close'], df['Open'])]
        ax2.bar(df['Date'], df['Volume'], color=colors, alpha=0.5)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.figures.append(('stock_price', fig))
        return fig
    
    def plot_returns_distribution(self):
        """Plot returns distribution and volatility"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        df = self.price_history.copy()
        returns = df['Close'].pct_change().dropna()
        
        # Histogram of returns
        ax1.hist(returns, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
        ax1.axvline(returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {returns.mean():.4f}')
        ax1.axvline(returns.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {returns.median():.4f}')
        ax1.set_title(f'{self.ticker} - Daily Returns Distribution', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Daily Return', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Rolling volatility
        rolling_vol = returns.rolling(window=30).std() * np.sqrt(252)  # Annualized
        ax2.plot(df['Date'][1:], rolling_vol, linewidth=1.5, color='darkred')
        ax2.set_title(f'{self.ticker} - 30-Day Rolling Volatility (Annualized)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Volatility', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.figures.append(('returns_volatility', fig))
        return fig
    
    def plot_risk_metrics(self):
        """Plot risk metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        risk_metrics = [
            ('Volatility_Annualized', 'Annualized Volatility', False),
            ('Sharpe_Ratio', 'Sharpe Ratio', False),
            ('Sortino_Ratio', 'Sortino Ratio', False),
            ('Max_Drawdown', 'Maximum Drawdown', True)
        ]
        
        for idx, (key, title, is_percent) in enumerate(risk_metrics):
            ax = axes[idx]
            
            if key in self.risk and self.risk[key] is not None:
                value = self.risk[key]
                if is_percent:
                    value = value * 100
                
                color = 'green' if (value > 0 and not is_percent) or (value > -20 and is_percent) else 'red'
                ax.bar([title], [abs(value) if value < 0 else value], color=color, alpha=0.7)
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')
                
                label = f'{value:.2f}%' if is_percent else f'{value:.4f}'
                ax.text(0, abs(value) if value < 0 else value, label, 
                       ha='center', va='bottom', fontweight='bold')
                
                if value < 0:
                    ax.set_ylim(bottom=0)
            else:
                ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                       transform=ax.transAxes, fontsize=12)
                ax.set_title(title, fontsize=12, fontweight='bold')
        
        plt.suptitle(f'{self.ticker} - Risk Metrics', fontsize=16, fontweight='bold')
        plt.tight_layout()
        self.figures.append(('risk_metrics', fig))
        return fig
    
    def plot_growth_metrics(self):
        """Plot growth rates"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        growth_data = {}
        for key, value in self.growth.items():
            if value is not None:
                clean_name = key.replace('_', ' ')
                growth_data[clean_name] = value * 100
        
        if growth_data:
            names = list(growth_data.keys())
            values = list(growth_data.values())
            colors = ['green' if v > 0 else 'red' for v in values]
            
            bars = ax.barh(names, values, color=colors, alpha=0.7)
            ax.set_xlabel('Growth Rate (%)', fontsize=12)
            ax.set_title(f'{self.ticker} - Growth Metrics', fontsize=16, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for bar, value in zip(bars, values):
                ax.text(value, bar.get_y() + bar.get_height()/2, 
                       f'{value:.2f}%', ha='left' if value > 0 else 'right', 
                       va='center', fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        self.figures.append(('growth_metrics', fig))
        return fig
    
    def create_all_plots(self):
        """Generate all plots"""
        print(f"\n{'='*60}")
        print(f"Creating visualizations for {self.ticker}")
        print(f"{'='*60}\n")
        
        plots = [
            ("Revenue & Net Income", self.plot_revenue_and_income),
            ("Balance Sheet", self.plot_balance_sheet),
            ("Cash Flows", self.plot_cash_flows),
            ("Profitability Ratios", self.plot_profitability_ratios),
            ("Financial Ratios Dashboard", self.plot_financial_ratios_dashboard),
            ("Stock Price", self.plot_stock_price),
            ("Returns & Volatility", self.plot_returns_distribution),
            ("Risk Metrics", self.plot_risk_metrics),
            ("Growth Metrics", self.plot_growth_metrics)
        ]
        
        for name, func in plots:
            try:
                print(f"Creating {name}...")
                func()
                print(f"  ✓ {name} created")
            except Exception as e:
                print(f"  ✗ Error creating {name}: {e}")
        
        print(f"\n✅ Created {len(self.figures)} visualizations")
    
    def save_all_plots(self, output_dir=None):
        """Save all plots to files"""
        if not output_dir:
            output_dir = f"stock_data/{self.ticker}/charts"
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving plots to {output_dir}...")
        
        for name, fig in self.figures:
            filepath = os.path.join(output_dir, f"{name}.png")
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"  ✓ Saved {name}.png")
        
        print(f"\n✅ All plots saved to {output_dir}")
    
    def show_all_plots(self):
        """Display all plots"""
        plt.show()


# =====================================
# USAGE
# =====================================
    def run_all(self):
        self.load_data()
        self.create_all_plots()
        self.save_all_plots()
if __name__ == "__main__":
    ticker = "AAPL"
    
    viz = FinancialVisualizer(ticker)
    viz.load_data()
    viz.create_all_plots()
    viz.save_all_plots()
    
    # Show plots
    #viz.show_all_plots()
    
    print("\n" + "="*60)
    print("VISUALIZATION COMPLETE")
    print("="*60)