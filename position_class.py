open_position, close_position = "open_position", "close_position"


class Position:
    def __init__(self, opening_price, opening_date, initial_value, book, trader, opening_order):
        self.opening_price = opening_price
        self.opening_date = opening_date
        self.value = initial_value
        self.money_removed_from_position = 0
        self.initial_value = initial_value
        self.book = book
        self.trader = trader
        self.opening_order = opening_order
        self.status = open_position
        self.final_closing_price = None
        self.closing_date = None
        self.all_closing_prices = []  # A list of (closing_price, weight) to calculate final closing price
        self.asset_quantity = initial_value / opening_order.compute_average_execution_price()  # Expressed in number of decimals of book.decimals

        self.trader.balance -= initial_value  # PAS PROPRE
        opening_order.link_orders_to_the_position(self)
        self.trader.opened_positions.append(self) # PAS PROPRE

    def compute_final_closing_price(self):
        average = 0
        for (price, weight) in self.all_closing_prices:
            average += price * weight
        self.final_closing_price = average

    def refresh_closing_prices(self, executed_order, average_price):
        weight = executed_order.amount / self.initial_value
        self.all_closing_prices.append((average_price, weight))

    def update_value(self, average_price):
        self.value = self.asset_quantity * average_price

    def reduce_position(self, closing_order, date):
        average_price = closing_order.compute_average_execution_price()
        executed_amount = closing_order.initial_amount - closing_order.amount
        self.money_removed_from_position += executed_amount
        self.asset_quantity -= executed_amount / average_price
        self.trader.balance += executed_amount
        self.refresh_closing_prices(closing_order, average_price)
        self.update_value(average_price)
        if abs(self.value) < 10**-2:
            self.closing_date = date
            self.status = close_position
            self.value = 0
            self.compute_final_closing_price()
            self.closing_date = date
            self.trader.opened_positions.remove(self)  # PAS PROPRE
            self.trader.closed_positions.append(self)
            closing_order.cancel()
