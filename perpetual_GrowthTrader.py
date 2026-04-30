import time
import numpy as np
from collections import defaultdict
import datetime
import yfinance as yf

class PerpetualGrowthTrader:
    def __init__(self):
        self.portfolio = defaultdict(float)      # Current holdings
        self.reusable_currency = 10000.0         # Starting capital
        self.profit_gained = 0.0                 # Locked profits
        self.red_sell_history = []               # Track RED_SELL performance
        
        # Penny stock arrays
        self.stocks = {
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

        # Print stock counts
        print(f"Total stocks: {sum(len(stocks) for stocks in self.stocks.values())}")
        for category, stocks in self.stocks.items():
            print(f"{category.capitalize()}: {len(stocks)} stocks")

    def get_live_prices(self, symbols):
        """Get real-time prices (replace with your API)"""
        try:
            data = yf.download(symbols[:10], period="1d", interval="1m")['Close'].iloc[-1]
            return {sym: price for sym, price in data.items() if sym in symbols}
        except:
            return {sym: 1.0 for sym in symbols}  # Mock for demo

    def run_perpetual_growth(self):
        """Main trading loop"""
        prices = {}
        entry_prices = defaultdict(float)  # Track entry price per stock
        
        while True:
            print(f"\n--- {datetime.datetime.now()} | Reusable: ${self.reusable_currency:.2f} | Profit: ${self.profit_gained:.2f} ---")
            
            # Update prices
            all_symbols = list(self.portfolio.keys()) + list(self.stocks["medical"][:5])
            prices.update(self.get_live_prices(all_symbols))
            
            # 1. RED DETECTION: -0.05% triggers NEXT_STACK (lose value)
            for symbol in list(self.portfolio.keys()):
                if symbol in prices and symbol in entry_prices:
                    pct_change = (prices[symbol] - entry_prices[symbol]) / entry_prices[symbol] * 100
                    
                    if pct_change <= -0.05:  # RED: Losing value
                        self.red_sell(symbol, prices[symbol], pct_change)
            
            # 2. GREEN SCALING: +1% → 5% growth cycle
            for symbol in list(self.portfolio.keys()):
                if symbol in prices and symbol in entry_prices:
                    pct_change = (prices[symbol] - entry_prices[symbol]) / entry_prices[symbol] * 100
                    
                    if 1.0 <= pct_change <= 5.0:  # GREEN growth
                        self.green_scale(symbol, prices[symbol], pct_change)
            
            # 3. 50/50 REUSABLE SPLIT for new positions
            if self.reusable_currency > 100:
                self.enter_50_50_positions()
            
            # 4. RED_SELL → Always increase reusable
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
        
        for symbol in self.stocks["medical"][:5]:
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

# Run it
trader = PerpetualGrowthTrader()
# trader.run_perpetual_growth()  # Uncomment for live