from book_class import Book
from psychology import init_of_the_traders
from trader_class import Trader

import matplotlib; matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import order_class as oc

nb_session_of_simulation = 120
number_of_traders = 50
book_list = []  # To able further development with multiple order books


def show_traders(traders_list):
    for trader in traders_list:
        print(trader)


def init_of_the_order_books():
    book_list.append(Book("BTC/USD", 0.25, 100000, 0))


def init_universe():
    specification_traders = init_of_the_traders(number_of_traders)
    list_traders = []
    for balance, risk_aversion, trading_frequency, independent_thinking, is_disruptive, is_insider, risk_ratio in specification_traders:
        list_traders.append(
            Trader(balance, risk_aversion, trading_frequency, independent_thinking, is_disruptive, is_insider,
                   risk_ratio))
    init_of_the_order_books()
    return list_traders


def process_trader(trader, book, session):
    amount = trader.think(book.get_sentiment())
    new_orders, immediate_process_orders = trader.create_new_position(book, amount, session)
    if new_orders is not None:
        oc.link_orders(new_orders)
    if immediate_process_orders is not None:
        book.add_orders(immediate_process_orders)
        book.process_pending_orders()


def refresh_price_graph(frame, book, session, ax, x, y, line):
    ax.set_title(
        f"Cours de l'actif: {round(book.transaction_prices[-1], 2)} USD\nMinute: {session}\nMarket Sentiment: {round(book.get_sentiment() * 100, 2)}\nSession Volume: {round(book.get_session_volume(), 2)} Total Volume: {round(book.get_total_volume(), 2)}")
    ax.set_xlim(frame - 200, 10 + frame)
    x.append(frame)
    y.append(book.transaction_prices[-1])
    line.set_data(x, y)


def refresh_depth_graph(book, session, ax, line):
    ax.set_title(
        f"Depth of {book.get_pair()}"
    )
    #min_price, max_price = book.get_min_max_price()
    max_quantity = book.get_max_order_quantity()
    min_price, max_price = 50000, 150000
    ax.set_xlim(min_price, max_price)
    ax.set_ylim(0, max_quantity*1.1)
    x, y = book.draw_depth()
    line.set_data(x, y)


def trading_action(frame, traders_list, book, x_time, y_price, price_ax, price_line, depth_ax, depth_line):
    global anim
    session = book.get_date()
    if frame % number_of_traders == 0:
        book.refresh_date()
        book.refresh_sentiment()

    trader = traders_list[frame % number_of_traders]
    process_trader(trader, book, session)
    refresh_price_graph(frame, book, session, price_ax, x_time, y_price, price_line)
    refresh_depth_graph(book, session, depth_ax, depth_line)
    return price_line, depth_line,


def run_simulation():
    traders_list = init_universe()
    global_book = book_list[0]
    x_time, y_price = [], []
    global_number_of_frames = number_of_traders * nb_session_of_simulation

    global_fig, global_ax = plt.subplots(ncols=2)

    # Configuration du graphique de prix
    price_line, = global_ax[0].plot([], [], lw=2)
    global_ax[0].set_xlim(0, 100)
    global_ax[0].set_ylim(0, 200000)
    global_ax[0].set_title(
        f"Cours de l'actif: {round(global_book.transaction_prices[0], 2)} USD\nMinute: {global_book.get_date()}\nMarket Sentiment: {round(global_book.get_sentiment() * 100, 2)}\nSession Volume: {global_book.get_session_volume()} Total Volume: {global_book.get_total_volume()}")
    global_ax[0].set_xlabel("Temps")
    global_ax[0].set_ylabel("Prix")

    # Configuration du graphique de profondeur
    depth_line, = global_ax[1].plot([], [], lw=2)
    global_ax[1].set_xlim(50000, 150000)
    global_ax[1].set_ylim(0, 200000)
    global_ax[1].set_title(
        f"Cours de l'actif: {round(global_book.transaction_prices[0], 2)} USD\nMinute: {global_book.get_date()}\nMarket Sentiment: {round(global_book.get_sentiment() * 100, 2)}")
    global_ax[1].set_xlabel("Price")
    global_ax[1].set_ylabel("Order Quantity")

    global_speed = 25

    global anim
    anim = FuncAnimation(
        fig=global_fig,
        func=trading_action,
        frames=global_number_of_frames,
        fargs=[traders_list, global_book, x_time, y_price, global_ax[0], price_line, global_ax[1], depth_line],
        interval=global_speed,
        repeat=False
    )
    plt.show()


run_simulation()
