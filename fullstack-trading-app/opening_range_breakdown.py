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
    SELECT id FROM strategy WHERE name = 'opening_range_breakdown'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    SELECT symbol, name
    FROM stock
    JOIN stock_strategy on stock_strategy.stock_id = stock.id
    WHERE stock_strategy.strategy_id=?
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]

current_date = date.today().isoformat()
NY = 'America/New_York'
# start_date = pd.Timestamp('2020-11-25 00:00', tz=NY).isoformat()
# end_date = pd.Timestamp('2020-11-25 23:59', tz=NY).isoformat()
start_date = pd.Timestamp(f'{current_date} 00:00', tz=NY).isoformat()
end_date = pd.Timestamp(f'{current_date} 23:59', tz=NY).isoformat()

# start_minute_bar='2020-11-25T09:30:00-05:00' 
# end_minute_bar='2020-11-25T09:45:00-05:00'
start_minute_bar=f"{current_date} 09:30:00-05:00" 
end_minute_bar=f"{current_date} 09:35:00-05:00" 

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders(status='all', limit=500, after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status !='canceled']

messages = []

for symbol in symbols:
  
    minute_bars = api.get_barset(symbol,'minute', start=start_date, end=end_date).df
    
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]
    opening_range_low = opening_range_bars.iloc[:,2].min()
    opening_range_high = opening_range_bars.iloc[:,1].max()
    opening_range = opening_range_high - opening_range_low
    
    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
    after_opening_range_breakdown = after_opening_range_bars[after_opening_range_bars.iloc[:,3]<opening_range_low]
    
    if not after_opening_range_breakdown.empty:
        if symbol not in existing_order_symbols:
            limit_price = after_opening_range_breakdown.iloc[0,3]
            # print(limit_price)
            print(opening_range_bars)
            print(opening_range_low)
            print(opening_range_high)
            print(opening_range)
            print(f"selling short {symbol} at {limit_price}, closed_below {opening_range_low} at {after_opening_range_breakdown.iloc[0]}")

            try:
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='limit',
                    qty='100',
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price - opening_range,
                    ),
                    stop_loss=dict(
                        stop_price=limit_price + opening_range,
                    )
                )
            except Exception as e:
                print(f"could not submit order {e}")
        else:
            print(f"Already have an order for {symbol}, skipping")