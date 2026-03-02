import sys

import ccxt


def check_revolut():
    print(f"CCXT Version: {ccxt.__version__}")
    if "revolut" in ccxt.exchanges:
        print("Revolut IS supported by CCXT.")
        exch = ccxt.revolut()
        print(f"Has fetchOHLCV: {exch.has.get('fetchOHLCV')}")
        print(f"Has fetchOrderBook: {exch.has.get('fetchOrderBook')}")
        print(f"Has fetchTicker: {exch.has.get('fetchTicker')}")
        print(f"Has fetchTickers: {exch.has.get('fetchTickers')}")
        print(f"Has fetchTrades: {exch.has.get('fetchTrades')}")
        print(f"Has fetchMyTrades: {exch.has.get('fetchMyTrades')}")
        print(f"Has fetchBalance: {exch.has.get('fetchBalance')}")
        print(f"Has fetchMarkets: {exch.has.get('fetchMarkets')}")
    else:
        print("Revolut is NOT supported in this CCXT version.")


if __name__ == "__main__":
    check_revolut()
