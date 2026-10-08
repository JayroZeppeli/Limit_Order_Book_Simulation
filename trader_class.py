from order_class import Order, Limit, StopLimit
from psychology import generate_bullishness, is_going_on_a_trade, generate_trade_specifications

buy, sell = "buy", "sell"  # Variables to avoid misspelling
market, limit, stop_limit = "market", "limit", "stop_limit"
open_position, close_position = "open_position", "close_position"


class Trader:
    trader_id = 0

    def __init__(self, balance, risk_aversion, trading_frequency, independent_thinking, is_disruptive, is_insider,
                 risk_ratio):
        self.trader_id = Trader.trader_id
        Trader.trader_id += 1
        self.balance = balance
        self.risk_aversion = risk_aversion  # A float x in [0, 1] => the trader is trading with 1-x % of his total balance
        self.trading_probability = trading_frequency / 43200  # An int x in [1, 43200] => the trader is trading an average of x times per month (43200 = 30*24*60)
        self.independent_thinking = independent_thinking  # A float x in [0, 1] => the impact of daily market sentiment on the trader
        self.is_disruptive = is_disruptive  # A bool, True => will trade against the daily market sentiment, False => The contrary
        self.is_insider = is_insider  # A bool, the insider will know exactly the next daily market sentiment
        self.risk_ratio = risk_ratio  # Determine the position of the take profit relatively to the stop loss  of every trade
        # We suppose that the risk ratio will be the same on every trade ex: 1:2 the trader is risking 1 lot to earn 2 lots on every trade
        # Here the trader has a risk ratio of 1:trader.risk_ratio
        self.opened_positions = []
        self.closed_positions = []

    def __str__(self):
        return f"Trader n°{self.trader_id}, Balance: {self.balance}$, Risk aversion: {self.risk_aversion}, Trading probability: {self.trading_probability}, " \
               f"Independent thinking: {self.independent_thinking}, Disruptive: {self.is_disruptive}, Insider: {self.is_insider}, Risk Ratio: 1:{self.risk_ratio}"

    def renew_order(self, order):
        order.cancel()
        if order.intention == open_position:
            return
        new_order = Order(order.book, order.trader, order.amount, order.book.get_date(), 100, close_position)
        order.book.market_execute(new_order)

    def get_independent_thinking(self):
        return self.independent_thinking

    def get_trading_probability(self):
        return self.trading_probability

    def think(self, daily_sentiment):
        if not is_going_on_a_trade(self):
            return 0
        bullishness = generate_bullishness(self, daily_sentiment)
        if abs(bullishness) < 0.1 or self.balance < 10:
            return 0
        amount = bullishness * self.risk_aversion * self.balance
        return amount

    def enter_with_market_order(self, book, amount, date, decimals, time_till_expiry, tp_price, sl_price):
        entering_order = Order(book, self, amount, date, time_till_expiry, open_position)

        take_profit_order = Limit(book, self, (-1) * amount, date, -1, tp_price, close_position)
        stop_loss_order = StopLimit(book, self, (-1) * amount, date, -1, sl_price, sl_price + 4 * decimals,
                                    close_position)
        return [entering_order, take_profit_order, stop_loss_order], [entering_order, take_profit_order, stop_loss_order]

    def enter_with_limit_order(self, book, amount, date, decimals, time_till_expiry, enter_price, tp_price, sl_price):

        take_profit_order = Limit(book, self, (-1) * amount, date, -1, tp_price, close_position)
        stop_loss_order = StopLimit(book, self, (-1) * amount, date, -1, sl_price, sl_price + 4 * decimals,
                                    close_position)
        entering_order = Limit(book, self, amount, date, time_till_expiry, enter_price, open_position,
                               [stop_loss_order, take_profit_order])
        return [entering_order, take_profit_order, stop_loss_order], [entering_order]

    def create_new_position(self, book, amount, date):
        precedent_price = book.estimated_price
        decimals = book.decimals
        if amount == 0:
            return None, None
        market_or_limit, time_till_expiry, accepted_loss, entering_spread = generate_trade_specifications()
        if amount > 0:
            enter_price = precedent_price - entering_spread * decimals  # Here this is an ask price
            tp_price = precedent_price + accepted_loss * self.risk_ratio - entering_spread * decimals
            sl_price = precedent_price - accepted_loss - entering_spread * decimals
        else:
            enter_price = precedent_price + entering_spread * decimals  # Here this is a bid price
            tp_price = precedent_price - accepted_loss * self.risk_ratio + entering_spread * decimals
            sl_price = precedent_price + accepted_loss + entering_spread * decimals
        if market_or_limit == 1:
            return self.enter_with_market_order(book, amount, date, decimals, time_till_expiry, tp_price, sl_price)
        else:
            return self.enter_with_limit_order(book, amount, date, decimals, time_till_expiry, enter_price, tp_price,
                                               sl_price)
