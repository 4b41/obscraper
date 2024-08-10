## obscraper

Orderbook scraping tool to log Level 2 data from the Binance.us api.

Uses threaded websocket clients to monitor individual symbols and writes incoming orders in txt files.

## Quickstart
Run the main.py script:
1. Clone repo: git clone https://github.com/4b41/obscraper.git
2. Select directory: cd obscraper/src
3. Compile program: python -u main.py
4. Create or remove watchers with the syntax: python main.py --create_watcher SYMBOL or python main.py --remove_watcher SYMBOL

Alternatively, you can run the code blocks in the main.ipynb notebook.
