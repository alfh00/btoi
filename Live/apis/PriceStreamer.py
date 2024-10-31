from pybitget.stream import BitgetWsClient, SubscribeReq, handel_error
from logger import Logger
from pybitget.enums import *
from pybitget import logger
import json
from models.live_prices import LiveStreamPrice
import threading


class PriceStreamer(threading.Thread):
    def __init__(self, shared_prices, price_lock: threading.Lock, price_events, candle_events):
        super().__init__()
        self.shared_prices = shared_prices  # Shared dictionary for price updates
        self.price_lock = price_lock        # Lock for thread-safe access to shared_prices
        self.price_events = price_events    # Events to notify when price is updated
        self.logger = Logger('PriceStreamer')
        self.ws_client = BitgetWsClient() \
            .error_listener(handel_error) \
            .build()
        # Subscribe to market channels
        self.symbols = shared_prices.keys()
        print(self.symbols)
        channels = [SubscribeReq("mc", "ticker", symbol) for symbol in self.symbols]
        self.ws_client.subscribe(channels, self.on_message)
    
    def on_message(self, message):

        data = json.loads(message)
        # print(data)
        if data['action'] == 'snapshot':
            # Extract the first entry from 'data' (which contains price information)
            price_data = data['data'][0]
            ts = data['ts']
            symbol=price_data['instId']
            tmp_data = dict(ts=ts, symbol=symbol, price=price_data['last'], ask=price_data['bestAsk'], bid=price_data['bestBid'], volume=price_data['baseVolume'])
            price = LiveStreamPrice(tmp_data)
            self.update_price(symbol, price)
    
    def update_price(self, symbol, price):
        with self.price_lock:
            self.shared_prices[symbol] = price
        # Notify TraderBot that a price update has occurred
        self.price_events[symbol].set()








        # """message: {'action': 'snapshot', 
        #     'arg': {'instType': 'mc', 'channel': 'ticker', 'instId': 'ARBUSDT'}, 
        #     'data': [{'instId': 'ARBUSDT', 
        #             'last': '0.5164', 
        #             'bestAsk': '0.5164', 
        #             'bestBid': '0.5162', 
        #             'high24h': '0.5199', 
        #             'low24h': '0.4979', 
        #             'priceChangePercent': '0.02501', 
        #             'capitalRate': '0.0001', 
        #             'nextSettleTime': 1730016000000, 
        #             'systemTime': 1730002543704, 
        #             'markPrice': '0.5167', 
        #             'indexPrice': '0.51703333', 
        #             'holding': '22779292.11', 
        #             'baseVolume': '5080613.79', 
        #             'quoteVolume': '2603798.222648', 
        #             'openUtc': '0.5143', 
        #             'chgUTC': '0.00408', 
        #             'symbolType': 1, '
        #             symbolId': 'ARBUSDT_UMCBL', 
        #             'deliveryPrice': '0', 
        #             'bidSz': '2621.09', 
        #             'askSz': '81.33'}], 
        #             'ts': 1730002543705}"""