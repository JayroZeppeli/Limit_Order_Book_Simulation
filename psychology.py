from random import randint
from numpy.random import binomial, uniform, normal


def init_of_the_traders(number_of_traders):
    traders_list = []
    for i in range(number_of_traders):
        balance = randint(10 ** 3, 10 ** 7)
        risk_aversion = uniform(0, 1)
        trading_frequency = randint(1, 43200)
        independent_thinking = uniform(0, 1)
        is_disruptive = bool(binomial(1, 0.01))
        is_insider = False  # bool(binomial(1, 0.0001))
        risk_ratio = uniform(1, 4)
        traders_list.append((balance, risk_aversion, trading_frequency, independent_thinking, is_disruptive, is_insider,
                             risk_ratio))
    return traders_list


def generate_new_market_sentiment(date, precedent_sentiment):
    new_sentiment = min(max(precedent_sentiment + normal(0, 0.1), -1), 1)
    return new_sentiment


def generate_bullishness(trader, daily_sentiment):
    personal_opinion = uniform(-1, 1)
    if trader.is_disruptive:
        daily_sentiment *= -1
    bullishness = daily_sentiment * (
            1 - trader.get_independent_thinking()) + personal_opinion * trader.get_independent_thinking()
    # Average between personal opinion and market sentiment, weighted by the independence
    return bullishness


def is_going_on_a_trade(trader):
    return bool(binomial(1, trader.get_trading_probability()))


def generate_trade_specifications():
    market_or_limit = binomial(1, 0.75)
    time_till_expiry = randint(1, 30)
    accepted_loss = randint(1, 10000)  # in number of decimals
    entering_spread = randint(0, 100)
    return market_or_limit, time_till_expiry, accepted_loss, entering_spread
