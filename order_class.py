from position_class import Position

buy, sell = "buy", "sell"  # Variables to avoid misspelling
market, limit, stop_limit = "market", "limit", "stop_limit"
open_position, close_position = "open_position", "close_position"
open_order, completed_order, cancelled_order = "open_order", "completed_order", "cancelled_order"


class Order:
    order_id = 0

    def __init__(self, book, trader, amount, date, time_till_expiry, intention,
                 orders_that_will_be_triggered_at_executions=None):
        if orders_that_will_be_triggered_at_executions is None:
            orders_that_will_be_triggered_at_executions = []
        self.book = book
        self.order_id = Order.order_id
        Order.order_id += 1
        self.trader = trader
        if amount > 0:
            self.side = buy
        else:
            self.side = sell
        self.amount = abs(amount)  # Amount left to be executed
        self.initial_amount = abs(amount)
        self.date = date  # An int from 0 to infinity (0 is the first session of the simulation)
        self.time_till_expiry = time_till_expiry  # An int from 1 to 10 080 (10080 = 7*24*60 correspond to 1 week of waiting in seconds)
        self.left_child = None  # A chain list of linked orders (to cancel them together at ease)
        self.status = "open"  # To know if the order is still on or not
        self.date_of_execution = None
        self.date_of_cancellation = None
        self.execution_prices = []
        self.intention = intention  # To know if it is in the intent to open or close a position
        self.linked_position = None  # Linked list to connect linked orders
        self.right_child = None
        self.presence = []  # To track where is the order (on which tables)
        self.stop_is_triggered = False
        self.in_the_upside = None
        self.orders_that_will_be_triggered_at_executions = orders_that_will_be_triggered_at_executions

    def __str__(self):
        """string = f"Market {self.side} Order on {self.book.pair}, Order ID: {self.order_id}, Trader ID: {self.trader.trader_id}," \
                 f" Date: {self.date}, Amount: {self.amount}$, Time till expiry: {self.time_till_expiry}, Status: {self.status}, " \
                 f"Completeness: {round(100 * (self.initial_amount - self.amount) / self.initial_amount, 2)}%" """
        string = f"Market Order ID: {self.order_id}"
        return string

    def get_side(self):
        return self.side

    def soustract_time_till_expiry(self):
        self.time_till_expiry -= 1
        if self.time_till_expiry == 0:
            self.trader.renew_order(self)

    def add_presence(self, prices_table, orders_table):
        self.presence.append((prices_table, orders_table))

    def remove_presence(self, prices_table, orders_table):
        self.presence.remove((prices_table, orders_table))

    def get_total_amount(self):
        return self.initial_amount

    def get_amount_left(self):
        return self.amount

    def get_brothers(self):
        brothers = [self]
        actual_order = self
        while actual_order.right_child is not None:
            actual_order = actual_order.right_child
            brothers.append(actual_order)
        actual_order = self
        while actual_order.left_child is not None:
            actual_order = actual_order.left_child
            brothers.append(actual_order)
        return brothers

    def compute_average_execution_price(self):
        average = 0
        for price, amount in self.execution_prices:
            average += price * amount / (self.initial_amount - self.amount)
        return round(average / len(self.execution_prices), 2)

    def link_orders_to_the_position(self, position):
        """Link all linked orders to the mentioned position"""
        brothers = self.get_brothers()
        for brother in brothers:
            brother.linked_position = position

    def cancel(self):
        if self in self.book.pending_orders:
            self.book.pending_orders.remove(self)
        if type(self) != Order:
            self.delete_order()
        self.status = cancelled_order
        if self.left_child is not None:
            self.left_child.right_child = None
            self.left_child.cancel()
        if self.right_child is not None:
            self.right_child.left_child = None
            self.right_child.cancel()

    def notify_order_executed(self, date):
        executed_amount = self.initial_amount - self.amount
        self.trigger_linked_orders()
        if self.intention == open_position:
            opening_price = self.compute_average_execution_price()
            Position(opening_price, date, executed_amount, self.book, self.trader, self)
        else:
            old_position = self.linked_position
            try:
                old_position.reduce_position(self, date)
            except AttributeError:
                print("Ordre sans position: ", self)
                print(f"Stop: {self.stop}")
                print(f"{[(str(o), o.price) for o in self.get_brothers()]}\n\n\n\n")
                self.cancel()

    def trigger_linked_orders(self):
        self.book.add_orders(self.orders_that_will_be_triggered_at_executions)

    def delete_order(self):
        """Not meant to be used for market orders"""
        return

    def get_price(self):
        print("Market order doesn't have limit price")
        return 0


class Limit(Order):

    def __init__(self, book, trader, amount, date, time_till_expiry, price, intention,
                 orders_that_will_be_triggered_at_executions=None):
        super().__init__(book, trader, amount, date, time_till_expiry, intention,
                         orders_that_will_be_triggered_at_executions)
        if orders_that_will_be_triggered_at_executions is None:
            orders_that_will_be_triggered_at_executions = []
        self.price = price

    def __str__(self):
        string = f"Limit Order ID: {self.order_id}"
        return string

    def get_price(self):
        return self.price

    def delete_order(self):
        self.book.remove_order_from_order_book(self)


class StopLimit(Order):

    def __init__(self, book, trader, amount, date, time_till_expiry, price, stop, intention, orders_that_will_be_triggered_at_executions=None):
        super().__init__(book, trader, amount, date, time_till_expiry, intention, orders_that_will_be_triggered_at_executions)
        self.price = price
        self.stop = stop
        self.stop_is_triggered = False

    def __str__(self):
        string = f"Stop Order ID: {self.order_id}"
        return string

    def remove_from_stop_waitlist(self):
        if self.in_the_upside is not None:
            if self.in_the_upside:
                price_index = self.book.table_of_stop_prices_on_the_upside.index(self.stop)
                prices_table, orders_table = self.book.table_of_stop_prices_on_the_upside, self.book.table_of_stop_orders_on_the_upside
            else:
                price_index = self.book.table_of_stop_prices_on_the_downside.index(self.stop)
                prices_table, orders_table = self.book.table_of_stop_prices_on_the_downside, self.book.table_of_stop_orders_on_the_downside
            orders_table[price_index].remove(self)
            if not orders_table[price_index]:  # Si c'était le dernier ordre à ce prix, on retire ce prix
                orders_table.pop(price_index)
                prices_table.pop(price_index)
            self.remove_presence(prices_table, orders_table)

    def delete_order(self):
        if self.stop_is_triggered:
            self.book.remove_order_from_order_book(self)
        else:
            self.remove_from_stop_waitlist()

    def get_price(self):
        return self.price

    def trigger_order(self):
        self.stop_is_triggered = True
        self.remove_from_stop_waitlist()
        self.book.process_limit_order(self)


def link_orders(order_list):
    if len(order_list) <= 1:
        return
    for i in range(1, len(order_list) - 1):
        order_list[i].left_child = order_list[i - 1]
        order_list[i].right_child = order_list[i + 1]

    order_list[0].left_child = None
    order_list[0].right_child = order_list[1]

    order_list[-1].left_child = order_list[-2]
    order_list[-1].right_child = None
