import asyncio
import pandas as pd
import numpy as np
import websockets
import json
from datetime import datetime, timezone
import certifi
import ssl
import matplotlib.pyplot as plt


def get_msg(currency):
    msg = \
        {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "public/get_tradingview_chart_data",
            "params": {
                "instrument_name": f"{currency}-PERPETUAL",
                "start_timestamp": start_date * 1000,
                "end_timestamp": end_date * 1000,
                "resolution": "1D"
            }
        }
    return json.dumps(msg)


async def call_api(msg):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with websockets.connect('wss://www.deribit.com/ws/api/v2', ssl=ssl_context) as websocket:
        await websocket.send(msg)
        response = await websocket.recv()
        return json.loads(response)


def get_ticks_and_prices(response):
    result = response['result']
    prices = np.array(result['close'])
    ticks = [datetime.fromtimestamp(epoch / 1000) for epoch in result['ticks']]
    return ticks, prices


prices_to_compare = {
    "ETH": 0.0013371,
    "BTC": 0.00005181,
    "DAI": 0.0015856,
    "SOL": 0.020195,
    "XRP": 7.2942,
    "ADA": 7.3376
}

start_date = int(datetime(2022, 1, 1, 8, tzinfo=timezone.utc).timestamp())
end_date = int(datetime(2025, 5, 8, 8, tzinfo=timezone.utc).timestamp())

dfs = []
for coin in ['BTC', 'ETH']:
    response = asyncio.run(call_api(get_msg(coin)))
    ticks, coin_usd = get_ticks_and_prices(response)
    usd_price = coin_usd * prices_to_compare[coin]
    dfs.append(pd.DataFrame({'date': ticks, 'coin': coin, 'coin_usd': coin_usd, 'usd_price': usd_price}))

df = pd.concat(dfs, ignore_index=True)
df = df.pivot(index='date', columns='coin', values='usd_price')
df['ETH-BTC'] = np.abs(df['ETH'] - df['BTC'])

plt.figure(figsize=(12, 6))
for coin in df.columns:
    plt.plot(df.index, df[coin], label=coin)

plt.title('USD Price of Coconut over Time')
plt.xlabel('Date')
plt.ylabel('USD Price')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

minimum = df.loc[df[['ETH-BTC']].idxmin()]['ETH-BTC']
minimum_date = minimum.index[0].strftime('%Y-%m-%d')
print(
    f"On {minimum_date} we observe the minimum distance between the price of the coconut in USD calculated using ETH and BTC exchange rates\n"
    f"Corresponding to a difference of {minimum.iloc[0]:.4f} USD"
)
coconut_price = df.loc[minimum.index]
print(
    f"On {minimum_date} the price in USD calculated using the ETH-USD rate is {coconut_price['ETH'].iloc[0]:.4f} USD\n"
    f"while the price in USD calculated using the BTC-USD rate is {coconut_price['BTC'].iloc[0]:.4f} USD\n"
)
