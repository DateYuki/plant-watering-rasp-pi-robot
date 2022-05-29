import os
import sys
import threading
from linebot import(LineBotApi, WebhookHandler)
from linebot.exceptions import(InvalidSignatureError)
from linebot.models import(MessageEvent, TextMessage, TextSendMessage)
from argparse import ArgumentParser
from flask import Flask, request, abort
from plant_water_server import PlantWaterServer

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('channel secret is None')
    sys.exit(1)
if channel_access_token is None:
    print('channel access token is None')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

plant_water_server = PlantWaterServer()

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text = True)
    app.logger.info("Request body:" + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
        
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    text = event.message.text
    
    if text.find('エバーフレッシュ') != -1:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'エバーフレッシュに水やりをします。'
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                '水やりをしています・・・'
            )
        )
        plant_water_server.plant1Watering()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'エバーフレッシュへの水やりが終わりました。'
            )
        )
        
    elif text.find('パキラ') != -1:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'パキラに水やりをします。\n\nこれから10日ごとに水やりします。'
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                '水やりをしています・・・'
            )
        )
        plant_water_server.plant2Watering()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'パキラへの水やりが終わりました。'
            )
        )
        
    elif text.find('水') != -1 or text.find('みず') != -1:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'どちらの植物に水やりしますか？\n  「エバーフレッシュ」\n  「パキラ」'
            )
        )
        
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                '''よくわかりません。\n「水やり」と「設定」を行うことができます。'''
            )
        )

def main():
    arg_parser = ArgumentParser(usage = 'Usage: python ' + __file__ + '[--port][--help]')
    arg_parser.add_argument('-p', '--port', default = 8000, help = 'port')
    arg_parser.add_argument('-d', '--debug', default = False, help = 'debug')
    options = arg_parser.parse_args()
    app.run(debug = options.debug, port = options.port)

if __name__ == "__main__":
    plant_water_server.rasp_pi_init()
    thread_1 = threading.Thread(target = main)
    thread_2 = threading.Thread(target = plant_water_server.regularWatering)
    thread_1.start()
    thread_2.start()