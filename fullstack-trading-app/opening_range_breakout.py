import sqlite3
import config
import alpaca_trade_api as tradeapi
import pandas as pd
import smtplib, ssl
from datetime import date

context = ssl.create_default_context()

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    SELECT id FROM strategy WHERE name = 'opening_range_breakout'
""")

strategy_id = cursor.fetchone()['id']

# print(strategy_id)

cursor.execute("""
    SELECT symbol, name
    FROM stock
    JOIN stock_strategy on stock_strategy.stock_id = stock.id
    WHERE stock_strategy.strategy_id=?
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]
# print(symbols)

current_date = date.today().isoformat()
NY = 'America/New_York'
# start_date = pd.Timestamp('2020-11-25 00:00', tz=NY).isoformat()
# end_date = pd.Timestamp('2020-11-25 23:59', tz=NY).isoformat()
start_date = pd.Timestamp(f'{current_date} 00:00', tz=NY).isoformat()
end_date = pd.Timestamp(f'{current_date} 23:59', tz=NY).isoformat()
# print(start_date)
# print(end_date)

# start_minute_bar='2020-11-25T09:30:00-05:00' 
# end_minute_bar='2020-11-25T09:45:00-05:00'
start_minute_bar=f"{current_date} 09:30:00-05:00" 
end_minute_bar=f"{current_date} 09:45:00-05:00" 

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', limit=500, after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status !='canceled']
# print(existing_order_symbols)
# minute_bars = api.get_barset("AAPL",'minute', start=start_date, end=end_date).df
# print(minute_bars)

messages = []

for symbol in symbols:
    minute_bars = api.get_barset(symbol,'minute', start=start_date, end=end_date).df
    # print(symbol)
    # print(minute_bars)
    # print(minute_bars.iloc[:,2].min())
    # print(minute_bars['low'])

    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
      
    opening_range_bars = minute_bars.loc[opening_range_mask]
    # print(opening_range_bars)

    # opening_range_low = opening_range_bars['low'].min()
    # opening_range_high = opening_range_bars['high'].max()
    # opening_range = opening_range_high - opening_range_low

    opening_range_low = opening_range_bars.iloc[:,2].min()
    opening_range_high = opening_range_bars.iloc[:,1].max()
    opening_range = opening_range_high - opening_range_low

    # print(opening_range_low)
    # print(opening_range_high)
    # print(opening_range)
    
    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]

    # print(after_opening_range_bars)
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars.iloc[:,3]>opening_range_high]

    if not after_opening_range_breakout.empty:
        if symbol not in existing_order_symbols:
            # print(after_opening_range_breakout)
            limit_price = after_opening_range_breakout.iloc[0,3]
            # print(limit_price)
            
            # message=f"placing order for {symbol} at {limit_price}, closed_above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]}\n\n"
            # messages.append(message)
            print(opening_range_bars)
            print(opening_range_low)
            print(opening_range_high)
            print(opening_range)
            print(f"placing order for {symbol} at {limit_price}, closed_above {opening_range_high} at {after_opening_range_breakout.iloc[0]}")

            try:
                api.submit_order(
                    symbol=symbol,
                    side='buy',
                    type='limit',
                    qty='100',
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price + opening_range,
                    ),
                    stop_loss=dict(
                        stop_price=limit_price - opening_range,
                    )
                )
            except Exception as e:
                print(f"could not submit order {e}")
        else:
            print(f"Already have an order for {symbol}, skipping")

# print(messages)

# with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
#     server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
#     email_message = f"Subject: Trade notifications for {current_date}\n\n"
#     email_message += "\n\n".join(messages)
#     server.sendmail(config.EMAIL_ADDRESS,config.EMAIL_ADDRESS, email_message)