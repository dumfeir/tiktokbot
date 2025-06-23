from flask import Flask
from threading import Thread

def keep_alive():
    app = Flask("")

    @app.route("/")
    def home():
        return "✅ Bot is alive!"

    def run():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run).start()
