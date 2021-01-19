#!/usr/bin/env python3
import sqlite3, config
import alpaca_trade_api as tradeapi
import numpy as np
import tulipy as ti
from datetime import date, timedelta

connection = sqlite3.connect(config.DB_FILE)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    SELECT id, symbol, name FROM stock
""")

rows = cursor.fetchall()

symbols = []
stock_dict = {}
for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

latest_day=date.today()-timedelta(days=1)
#remember to edit this line according to when you are running cron job

cursor.execute("""
    DELETE FROM stock_price
""")

chunk_size = 200
for i in range(0, len(symbols), chunk_size):
    symbol_chunk = symbols[i:i+chunk_size]
    barsets = api.get_barset(symbol_chunk, 'day')
    for symbol in barsets:
        
        print(f"processing symbol {symbol}")

        # print(barsets[symbol])

        recent_closes = [bar.c for bar in barsets[symbol]]

        # print(rsi_14)
        # print(sma_20)
        # print(sma_50)

        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]
        
            # print(latest_day.isoformat())
            # print(bar.t.date().isoformat())
            # print(type(latest_day.isoformat()))
            # print(type(bar.t.date().isoformat()))

            if len(recent_closes)>=50 and latest_day.isoformat() == bar.t.date().isoformat():

                sma_20 = ti.sma(np.array(recent_closes), period=20)[-1]
                sma_50 = ti.sma(np.array(recent_closes), period=50)[-1]
                rsi_14 = ti.rsi(np.array(recent_closes), period=14)[-1]
            else:
                sma_20, sma_50, rsi_14 = None, None, None

            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma_50, rsi_14))
connection.commit()

# barsets = api.get_barset(['Z'], 'minute')
# # print(barsets)

# for symbol in barsets:
#     print(f"processing symbol {symbol}")

#     for bar in barsets[symbol]:
#         print (bar.t, bar.o, bar.h, bar.l, bar.c, bar.v)