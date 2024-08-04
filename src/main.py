import websocket
import threading
import json
import time
import argparse
import queue
import os

watchers = {}
writers = {}

def get_unix_time():
    return time.time_ns() // 1000

class Client(threading.Thread):
    def __init__(self, url, exchange, interval):
        super().__init__()
        self.ws = websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        self.exchange = exchange
        self.interval = interval
        self.stop_event = threading.Event()

    def run(self):
        self.ws.run_forever(ping_interval = self.interval)

    def close(self):
        self.stop_event.set()
        if self.ws:
            self.ws.close()

    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(f"{self.exchange} Error: {error}")

    def on_close(self, ws, error_status, error_message):
        print(f"{self.exchange} Closed. Error Status: {error_status}. Error Message: {error_message}")

    def on_open(self, ws):
        print(f'Connected to {self.exchange}\n')

class SymbolWatcher(Client):
    def __init__(self, symbol, depth, interval):
        url = f"wss://stream.binance.us:9443/ws/{symbol}@depth{depth}"
        self.message_buffer = queue.Queue()
        self.symbol = symbol
        super().__init__(url, "Binance", interval)
        print("Watcher created successfully")

    def on_message(self, ws, message):
        self.message_buffer.put(message)
    
    def write_to_file(self):
        with open(f"{self.symbol}.txt", 'a') as file:
            while not self.stop_event.is_set() or not self.message_buffer.empty():
                try:
                    message = self.message_buffer.get(timeout=1)
                    data = json.loads(message)
                    bids = data["bids"]
                    asks = data["asks"]
                    for i in range(min(len(bids), len(asks))):
                        entry = f"{data['lastUpdateId']}, {get_unix_time()}, {bids[i][0]}, {asks[i][0]}, {bids[i][1]}, {asks[i][1]}\n"
                        file.write(entry)
                except queue.Empty:
                    continue
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")

def create_watcher(args):
    global watchers
    global writers

    symbol = args.create_watcher

    if not os.path.exists(f"{symbol}.txt"):
        try:
            with open(f"{symbol}.txt", 'w') as file:
                file.write("TIMEID UNIXTIME BID ASK BIDSIZE OFFERSIZE\n")
            print(f"File '{symbol}.txt' created.")
        except IOError as e:
            print(f"Error occurred while writing to the file: {e}")

    ws_client = SymbolWatcher(symbol,10,10000)
    ws_client_writer = threading.Thread(target=ws_client.write_to_file)

    watchers[symbol] = ws_client
    writers[symbol] = ws_client_writer
    
    ws_client.start()
    ws_client_writer.start()

def remove_watcher(args):
    symbol = args.remove_watcher

    watcher = watchers[symbol]
    writer = writers[symbol]
    
    watcher.close()

    watcher.join()
    writer.join()

def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create_watcher",
        default="EMPTY"
    )
    parser.add_argument(
        "--remove_watcher",
        default="EMPTY"
    )
    return parser.parse_args();


if __name__ == '__main__':
    args = parser()
    if (args.create_watcher != "EMPTY"):
        create_watcher(args)
    if (args.remove_watcher != "EMPTY" ):
        remove_watcher(args)