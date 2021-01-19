import config
import websocket, json

print(config.API_KEY)
print(config.SECRET_KEY)
def on_open(ws):
    print("opened")
    #auth_data = {"action": "authenticate","data": {"key_id": config.API_KEY, "secret_key": config.SECRET_KEY}}
    auth_data={"action": "authenticate","data": {"key_id": "PKBSAVUI8HH1J0UJQ128", "secret_key": "JeUdFPimv8PWlSPfEzARdYAstZfpmwAJWgdCO3v6"}}
    ws.send(json.dumps(auth_data))

    listen_message = {"action": "listen", "data": {"streams": ["AM.SPY"]}}

    ws.send(json.dumps(listen_message))

def on_message(ws, message):
    print("received a message")
    print(message)

def on_close(ws):
    print("closed connection")

socket = "wss://data.alpaca.markets/stream"

ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_close=on_close)
ws.run_forever()

#{"action": "authenticate","data": {"key_id": "PKAMETL7XYQYKV1F3SXR", "secret_key": "ez1oCI3h33yIy91LrXS2z96STr3m7nlWXRAxW07d"}}