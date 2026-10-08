from bisect import insort

import psychology
from order_class import Order, Limit, StopLimit

buy, sell = "buy", "sell"  # Variables to avoid misspelling


def is_equal_to(number_a, number_b):
    distance = abs(number_a - number_b)
    return distance < 10**-2


def insert_while_sorted(table, element, is_increasing):
    if is_increasing:
        insort(table, element)
    else:
        table.reverse()
        insort(table, element)
        table.reverse()


def insert_new_order(list_of_prices, list_of_orders, price, order, is_increasing):
    if price not in list_of_prices:
        insert_while_sorted(list_of_prices, price, is_increasing)
        index_price = list_of_prices.index(price)
        list_of_orders.insert(index_price, [])
    else:
        index_price = list_of_prices.index(price)
    list_of_orders[index_price].append(order)
    order.add_presence(list_of_prices, list_of_orders)


def format_decimals(order):
    if type(order) != Order:
        order.price = round(order.price, 2)


class Book:
    def __init__(self, pair, decimals, start_price, date):
        self.estimated_price = start_price
        self.transaction_prices = [start_price]
        self.pair = pair  # The trading pair ex: "BTC/USD"
        self.decimals = decimals  # The decimals in which the trades will be computed ex: 0.000125
        self.deposited_volume = 0  # Total dollars locked in the order book waiting to be executed
        self.executed_volume = 0  # Total dollars executed
        self.sentiment = 0  # Float x in [-1, 1] that represents the market sentiment
        self.table_of_ask_prices = []  # Sorted list of prices
        self.table_of_ask_orders = []  # list of lists of orders at a certain price (the index corresponds to the table above)
        self.table_of_bid_prices = []
        self.table_of_bid_orders = []
        self.table_of_stop_prices_on_the_upside = []
        self.table_of_stop_orders_on_the_upside = []  # Table of stop orders waiting to be triggered on the upside of the price
        self.table_of_stop_prices_on_the_downside = []
        self.table_of_stop_orders_on_the_downside = []
        self.pending_orders = []
        self.date = date
        self.session_volume = 0
        self.total_volume = 0

    def __str__(self):
        string = ""
        space = "                   "
        total_bid = 0
        total_ask = 0
        string += f"Price{space}Amount\n(USD){space}(USD)\n"
        for price_index in range(len(self.table_of_bid_prices) - 1, -1, -1):
            bid_price = self.table_of_bid_prices[price_index]
            total_bid += self.calculate_total_bids_at(price_index)
            string += f"{round(bid_price, 2)}{space}{round(total_bid, 2)}\n"
        if self.table_of_bid_prices != [] and self.table_of_ask_prices != []:
            self.estimated_price = round((self.table_of_bid_prices[0] + self.table_of_ask_prices[0]) / 2, 2)
        string += f"\nPRICE: {self.estimated_price}\n\n"
        for price_index in range(len(self.table_of_ask_prices)):
            ask_price = self.table_of_ask_prices[price_index]
            total_ask += self.calculate_total_asks_at(price_index)
            string += f"{round(ask_price, 2)}{space}{round(total_ask, 2)}\n"
        total = total_bid + total_ask
        if total == 0:
            bid_percent, ask_percent = 0, 0
        else:
            ask_percent = round(total_ask / total * 100, 2)
            bid_percent = round(total_bid / total * 100, 2)
        string += f"ASK: {ask_percent}%{space}BID: {bid_percent}%\n"
        string += f"ASK: {round(total_ask, 2)}${space}BID: {round(total_bid, 2)}$\n"
        return string

    def add_volume(self, transaction_amount):
        self.session_volume += transaction_amount
        self.total_volume += transaction_amount

    def get_session_volume(self):
        return self.session_volume

    def get_total_volume(self):
        return self.total_volume

    def get_pair(self):
        return self.pair

    def refresh_previous_prices(self):
        self.transaction_prices = [self.transaction_prices[-1]]

    def refresh_date(self):
        self.date += 1
        self.session_volume = 0
        self.refresh_all_orders_date()

    def refresh_all_orders_date(self):
        table_table_table_orders = [self.table_of_bid_orders, self.table_of_ask_orders, self.table_of_stop_orders_on_the_upside, self.table_of_stop_orders_on_the_downside]
        for table_table_orders in table_table_table_orders:
            for table_order in table_table_orders:
                for order in table_order:
                    order.soustract_time_till_expiry()

    def refresh_sentiment(self):
        daily_sentiment = psychology.generate_new_market_sentiment(self.date, self.sentiment)
        self.sentiment = daily_sentiment

    def get_date(self):
        return self.date

    def get_sentiment(self):
        return self.sentiment

    def get_min_max_price(self):
        if not self.table_of_ask_prices or not self.table_of_bid_prices:
            return 0, 0
        return self.table_of_ask_prices[-1], self.table_of_bid_prices[-1]

    def get_max_order_quantity(self):
        sum_asks, sum_bids = 0, 0
        for table_order in self.table_of_ask_orders:
            for order in table_order:
                sum_asks += order.get_amount_left()
        for table_order in self.table_of_bid_orders:
            for order in table_order:
                sum_bids += order.get_amount_left()
        return max(sum_asks, sum_bids)

    def draw_depth(self):
        x = []
        y = []
        for price_index in range(len(self.table_of_ask_prices)):
            x.insert(0, self.table_of_ask_prices[price_index])
            y.insert(0, 0)
            if len(y) > 1:
                y[0] += y[1]
            for order in self.table_of_ask_orders[price_index]:
                y[0] += order.get_amount_left()
        first = True
        if self.table_of_ask_prices and self.table_of_bid_prices:
            x.append((self.table_of_bid_prices[0] + self.table_of_ask_prices[0]) / 2)
            y.append(0)
        elif self.table_of_bid_prices:
            x.append(self.table_of_bid_prices[0] - self.decimals)
            y.append(0)
        elif self.table_of_ask_prices:
            x.append(self.table_of_ask_prices[0] + self.decimals)
            y.append(0)
        for price_index in range(len(self.table_of_bid_prices)):
            x.append(self.table_of_bid_prices[price_index])
            y.append(0)
            if not first:
                y[-1] += y[-2]
            for order in self.table_of_bid_orders[price_index]:
                y[-1] += order.get_amount_left()
            first = False
        return x, y

    def remove_order_from_order_book(self, order, price_index=None):
        # rajouter un assert si l'ordre n'est pas un limite
        if order.get_side() == sell:
            orders_table = self.table_of_bid_orders
            prices_table = self.table_of_bid_prices
            if order.get_price() not in prices_table:
                return
            if price_index is None:
                price_index = prices_table.index(order.get_price())
        else:
            orders_table = self.table_of_ask_orders
            prices_table = self.table_of_ask_prices
            if order.get_price() not in prices_table:
                return
            if price_index is None:
                price_index = prices_table.index(order.get_price())
        orders_table[price_index].remove(order)
        if not orders_table[price_index]:  # Si c'était le dernier ordre à ce prix, on retire ce prix
            orders_table.pop(price_index)
            prices_table.pop(price_index)
        order.remove_presence(prices_table, orders_table)

    def trigger_stop_orders(self, price):
        while self.table_of_stop_prices_on_the_upside and price - self.table_of_stop_prices_on_the_upside[0] >= 10**-2:
            for order in self.table_of_stop_orders_on_the_upside[0]:
                order.trigger_order()
        while self.table_of_stop_prices_on_the_downside and self.table_of_stop_prices_on_the_downside[0] - price >= 10**-2:
            for order in self.table_of_stop_orders_on_the_downside[0]:
                order.trigger_order()

    def notify_book_execution(self, execution_price, order_to_remove):
        self.transaction_prices.append(execution_price)
        if order_to_remove is not None:
            self.session_volume += order_to_remove.get_total_amount()
            self.total_volume += order_to_remove.get_total_amount()
            self.remove_order_from_order_book(order_to_remove, 0)
        self.trigger_stop_orders(execution_price)  # Le problème c'est qu'il ne faut pas juste des stops en fait pour les limites, il faut carrément une waitlist avec un order_id associé, et quand il est éxécuté on le lance

    def execute_transaction(self, maker, taker):
        if is_equal_to(maker.amount, taker.amount):
            executed_amount = taker.amount
            taker.amount = 0  # 0 = order.amount - executed_amount
            maker.amount = 0
            taker.execution_prices.append((maker.price, executed_amount))
            maker.execution_prices.append((maker.price, executed_amount))
            taker.notify_order_executed(self.date)
            maker.notify_order_executed(self.date)
            self.notify_book_execution(maker.price, maker)
            return 1
        if maker.amount > taker.amount:
            executed_amount = taker.amount
            maker.amount -= executed_amount
            maker.execution_prices.append((maker.price, executed_amount))
            taker.execution_prices.append((maker.price, executed_amount))
            taker.amount = 0
            taker.notify_order_executed(self.date)
            self.notify_book_execution(maker.price, None)
            return 1
        else:
            executed_amount = maker.amount
            taker.amount -= executed_amount
            maker.amount = 0
            taker.execution_prices.append((maker.price, executed_amount))
            maker.execution_prices.append((maker.price, executed_amount))
            maker.notify_order_executed(self.date)
            self.notify_book_execution(maker.price, maker)
            return 0

    def process_buy_limit_order(self, order):
        while self.table_of_bid_prices != [] and order.get_price() >= self.table_of_bid_prices[0]:
            if self.execute_transaction(self.table_of_bid_orders[0][0], order):
                return 1
        insert_new_order(self.table_of_ask_prices, self.table_of_ask_orders, order.price, order, False)

    def process_sell_limit_order(self, order):
        while self.table_of_ask_prices != [] and order.get_price() <= self.table_of_ask_prices[0]:
            if self.execute_transaction(self.table_of_ask_orders[0][0], order):
                return 1
        insert_new_order(self.table_of_bid_prices, self.table_of_bid_orders, order.get_price(), order, True)

    def process_limit_order(self, order):
        if order.get_side() == buy:
            self.process_buy_limit_order(order)
        else:
            self.process_sell_limit_order(order)

    def market_execute(self, order):
        if order.get_side() == buy:
            prices_table = self.table_of_bid_prices
            order_table = self.table_of_bid_orders
        else:
            prices_table = self.table_of_ask_prices
            order_table = self.table_of_ask_orders
        if not prices_table:
            order.cancel()
            return 0
        while prices_table:
            limit_order = order_table[0][0]
            if self.execute_transaction(limit_order, order):
                return 1
        order.cancel()
        return 0

    def process_stop_limit_order(self, order):
        if order.stop == self.estimated_price:
            order.trigger_order()
        elif order.stop > self.estimated_price:
            order.in_the_upside = True
            insert_new_order(self.table_of_stop_prices_on_the_upside, self.table_of_stop_orders_on_the_upside,
                             order.stop, order, True)
        else:
            order.in_the_upside = False
            insert_new_order(self.table_of_stop_prices_on_the_downside, self.table_of_stop_orders_on_the_downside,
                             order.stop, order, False)

    def calculate_total_bids_at(self, price_index):
        total = 0
        for order in self.table_of_bid_orders[price_index]:
            total += order.get_amount_left()
        return total

    def calculate_total_asks_at(self, price_index):
        total = 0
        for order in self.table_of_ask_orders[price_index]:
            total += order.get_amount_left()
        return total

    def add_orders(self, orders):
        for order in orders:
            self.pending_orders.append(order)

    def process_pending_orders(self):
        while self.pending_orders:
            order = self.pending_orders.pop(0)
            if type(order) == Order:
                self.market_execute(order)
            elif type(order) == Limit:
                self.process_limit_order(order)
            elif type(order) == StopLimit:
                self.process_stop_limit_order(order)
