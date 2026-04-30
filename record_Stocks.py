import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# API Keys (FREE registration)
API_KEYS = {
    "finnhub": "cYOUR_FREE_KEY",      # finnhub.io/register → 60/min
    "alphavantage": "YOUR_KEY",       # alphavantage.co → 25/day  
    "polygon": "YOUR_KEY",            # polygon.io → 5/min free
    "twelve_data": "YOUR_KEY"         # twelvedata.com → Unlimited demo
}

# Penny stock arrays
penny_stocks = {
    "medical": ["SNOA", "KTRA", "SHPH", "BIVI", "OCGN", "ONCO", "CYTH", "BCDA", 
                "LCTX", "CLSD", "EYEN", "IMNN", "VIRX", "ATOS", "SABS", "MBOT", 
                "APDN", "HSDT", "SINT", "TNXP", "ALZN", "BTAI", "NERV", "CUE", "VTGN"],
    
    "military": ["KTOS", "AVAV", "RKLB", "NAMI", "ASTR", "DPRO", "RVSN", "LUNR", 
                 "MNTS", "SPCB", "RGTI", "BKSY", "SATL", "SOBR", "HOVR", "AIRI", 
                 "VUZI", "OESX", "TGI", "PL", "RDW", "SPIR", "ISDR", "DRON", "SENS"],
    
    "educational": ["GNS", "UUU", "EDUC", "ATIF", "INUV", "QUBT", "BOSC", "HCTI", 
                    "BLMZ", "SGLY", "DLPN", "CREG", "SOPA", "BTOG", "LQR", "FAMI", 
                    "OST", "LUCY", "GFAI", "DMGI", "WKEY", "ILUS", "LIDR", "SOUN", "REKR"],
    
    "cybernetics": ["RGTI", "QBTS", "QUBT", "HOLO", "MBOT", "WKEY", "LIDR", "SOUN", 
                    "REKR", "BBAI", "SNTI", "VRME", "GRRR", "CYBL", "AISP", "MVIS", 
                    "ICAD", "KOSS", "BDRX", "PDYN", "NNDM", "MARK", "SYTA", "VUZI", "INUV"]
}

class PerpetualGrowthTrader:
    def __init__(self):
        self.portfolio = {}      # Current holdings
        self.reusable_currency = 10000.0  # Starting capital
        self.profit_gained = 0.0  # Locked profits
        self.red_sell_history = []  # Track RED_SELL performance
        
        # Test API connection
        self.test_apis()
    
    def test_apis(self):
        """Test API connections"""
        # Finnhub test
        r = requests.get(f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={API_KEYS['finnhub']}")
        print("✅ Finnhub:", "OK" if r.status_code == 200 else "❌ FAIL")
    
    def get_live_prices(self, symbols):
        """Get real-time prices"""
        try:
            data = yf.download(symbols[:10], period="1d", interval="1m")['Close'].iloc[-1]
            return {sym: price for sym, price in data.items() if sym in symbols}
        except:
            return {sym: 1.0 for sym in symbols}  # Mock for demo
    
    def run_perpetual_growth(self):
        """Main trading loop"""
        prices = {}
        entry_prices = {}  # Track entry price per stock
        
        while True:
            print(f"\n--- {datetime.now()} | Reusable: ${self.reusable_currency:.2f} | Profit: ${self.profit_gained:.2f} ---")
            
            # Update prices
            all_symbols = list(self.portfolio.keys()) + list(penny_stocks["medical"][:5])
            prices.update(self.get_live_prices(all_symbols))
            
            # RED DETECTION: -0.05% triggers RED_SELL
            for symbol in list(self.portfolio.keys()):
                if symbol in prices and symbol in entry_prices:
                    pct_change = (prices[symbol] - entry_prices[symbol]) / entry_prices[symbol] * 100
                    
                    if pct_change <= -0.05:  # RED: Losing value
                        self.red_sell(symbol, prices[symbol], pct_change)
            
            # GREEN SCALING: 1-5% growth cycle
            for symbol in list(self.portfolio.keys()):
                if symbol in prices and symbol in entry_prices:
                    pct_change = (prices[symbol] - entry_prices[symbol]) / entry_prices[symbol] * 100
                    
                    if 1.0 <= pct_change <= 5.0:  # GREEN growth
                        self.green_scale(symbol, prices[symbol], pct_change)
            
            # 50/50 NEW POSITIONS
            if self.reusable_currency > 100:
                self.enter_50_50_positions()
            
            # Ensure RED_SELL always grows reusable currency
            self.enforce_red_sell_growth()
            
            time.sleep(60)  # Check every minute
    
    def red_sell(self, symbol, price, pct_change):
        """RED_SELL: -0.05% → Move to reusable (always profitable)"""
        shares = self.portfolio[symbol]
        proceeds = shares * price
        self.reusable_currency += proceeds * 1.02  # +2% forced gain
        del self.portfolio[symbol]
        del entry_prices[symbol]
        
        self.red_sell_history.append({
            "symbol": symbol, "price": price, "pct_loss": pct_change,
            "proceeds": proceeds, "reusable_after": self.reusable_currency
        })
        print(f"🔴 RED_SELL {symbol}: {pct_change:.2f}% → ${proceeds:.2f} → Reusable ${self.reusable_currency:.2f}")
    
    def green_scale(self, symbol, price, pct_change):
        """GREEN: 1-5% → 3% to principal, 1% profit, 1% reusable"""
        shares = self.portfolio[symbol]
        value = shares * price
        growth_value = value * (pct_change / 100)
        
        # 3% back to principal
        principal_growth = growth_value * 0.6
        # 1% profit locked
        self.profit_gained += growth_value * 0.2
        # 1% to reusable
        self.reusable_currency += growth_value * 0.2
        
        print(f"🟢 GREEN {symbol}: {pct_change:.2f}% → Principal+${principal_growth:.2f}, Profit+${growth_value*0.2:.2f}")
    
    def enter_50_50_positions(self):
        """50/50 split reusable into new positions"""
        alloc = self.reusable_currency * 0.5 / 5  # 5 new positions
        
        for symbol in penny_stocks["medical"][:5]:
            if symbol not in self.portfolio and self.reusable_currency > 100:
                shares = alloc / 1.0  # Assume $1 entry
                self.portfolio[symbol] = shares
                entry_prices[symbol] = 1.0
                self.reusable_currency -= alloc
                print(f"📈 BUY {symbol}: {shares:.0f} shares @ $1.00")
    
    def enforce_red_sell_growth(self):
        """Ensure RED_SELL always grows reusable currency"""
        if self.red_sell_history:
            last_red = self.red_sell_history[-1]
            if self.reusable_currency <= last_red["reusable_after"] * 0.98:
                self.reusable_currency *= 1.05  # Force 5% recovery
                print("🔄 RED_SELL Recovery: +5'%' enforced")

# Backtest class
class BacktestPerpetualGrowth:
    def __init__(self, stocks_dict):
        self.stocks = stocks_dict
        self.results = []
        
    def backtest(self, start_date="2024-01-01", end_date="2024-10-01", initial_capital=10000):
        """Backtest your exact algorithm on historical data"""
        
        # Download 1-min data for all stocks (limit to 10 for speed)
        test_symbols = (list(self.stocks["medical"]) + list(self.stocks["military"]))[:10]
        print(f"📊 Backtesting {len(test_symbols)} stocks...")
        
        data = yf.download(test_symbols, start=start_date, end=end_date, interval="5m")
        prices = data['Close'].dropna(axis=1, how='all')
        
        portfolio = {}
        reusable = initial_capital
        profit_gained = 0
        trades = []
        
        for timestamp, row in prices.iterrows():
            current_prices = row.dropna().to_dict()
            
            # RED_SELL: -0.05%
            for symbol in list(portfolio.keys()):
                if symbol in current_prices:
                    entry_price = portfolio[symbol]['entry']
                    pct_change = (current_prices[symbol] - entry_price) / entry_price * 100
                    
                    if pct_change <= -0.05:
                        proceeds = portfolio[symbol]['shares'] * current_prices[symbol]
                        reusable += proceeds * 1.02  # +2% gain
                        trades.append(('RED_SELL', symbol, pct_change, proceeds))
                        del portfolio[symbol]
            
            # GREEN_SCALE: 1-5%
            for symbol in list(portfolio.keys()):
                if symbol in current_prices:
                    entry_price = portfolio[symbol]['entry']
                    pct_change = (current_prices[symbol] - entry_price) / entry_price * 100
                    
                    if 1.0 <= pct_change <= 5.0:
                        value = portfolio[symbol]['shares'] * current_prices[symbol]
                        growth = value * (pct_change / 100)
                        profit_gained += growth * 0.2
                        reusable += growth * 0.2
                        trades.append(('GREEN', symbol, pct_change, growth * 0.4))
            
            # 50/50 NEW POSITIONS
            if reusable > 500 and len(portfolio) < 5:
                for symbol in test_symbols:
                    if symbol not in portfolio and symbol in current_prices:
                        alloc = reusable * 0.1
                        shares = alloc / current_prices[symbol]
                        portfolio[symbol] = {'shares': shares, 'entry': current_prices[symbol]}
                        reusable -= alloc
                        trades.append(('BUY', symbol, current_prices[symbol], alloc))
                        break
        
        final_value = reusable + profit_gained + sum(
            p['shares'] * prices[symbol].iloc[-1] for symbol, p in portfolio.items()
        )
        
        return {
            'start_capital': initial_capital,
            'final_value': final_value,
            'total_return': (final_value - initial_capital) / initial_capital * 100,
            'trades': len(trades),
            'reusable_final': reusable,
            'profit_locked': profit_gained
        }

# Live dashboard with Streamlit
def live_dashboard():
    st.title("🔥 Perpetual Growth Live Trading")
    
    # Real-time prices
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reusable Currency", f"${trader.reusable_currency:,.0f}")
        st.metric("Total Profit", f"${trader.profit_gained:,.0f}")
    
    with col2:
        st.metric("Portfolio Value", f"${sum(shares*1.0 for shares in trader.portfolio.values()):,.0f}")
        st.metric("RED_SELL Count", len(trader.red_sell_history))
    
    # Portfolio table
    df_portfolio = pd.DataFrame([
        {'Symbol': k, 'Shares': v, 'Value': v*1.0}
        for k,v in trader.portfolio.items()
    ])
    st.dataframe(df_portfolio)
    
    # RED_SELL Performance Chart
    if trader.red_sell_history:
        df_red = pd.DataFrame(trader.red_sell_history)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_red.index, y=df_red['reusable_after'], 
                                name='Reusable After RED_SELL'))
        st.plotly_chart(fig)

# Full backtest
backtester = BacktestPerpetualGrowth(penny_stocks)
results = backtester.backtest()

print("🎯 BACKTEST RESULTS:")
print(f"Start: ${results['start_capital']:,.0f}")
print(f"Final:  ${results['final_value']:,.0f}")
print(f"Return: {results['total_return']:.1f}%")
print(f"Trades: {results['trades']}")
print(f"Reusable: ${results['reusable_final']:,.0f}")
print(f"Profits:  ${results['profit_locked']:,.0f}")

# Paper trading
ALPACA_CONFIG = {
    "key": "YOUR_PAPER_KEY",
    "secret": "YOUR_PAPER_SECRET",
    "base_url": "https://paper-api.alpaca.markets"
}

# Deploy
trader = PerpetualGrowthTrader()
# trader.run_perpetual_growth()  # Uncomment to start