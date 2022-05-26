import os
import sys
from linebot import(LineBotApi, WebhookHandler)
from linebot.exceptions import(InvalidSignatureError)
from linebot.models import(MessageEvent, TextMessage, TextSendMessage)
from argparse import ArgumentParser
from flask import Flask, request, abort

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
    
    if text.find('エバーフォレスト') != -1:
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'おっけー、エバーフォレストに水やりするで！\n\nほんでこれから7日ごとに水やりしとくわ。ペース変えたいなら教えてな。'
            )
        )
        
    elif text.find('パキラ') != -1:
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'おっけー、パキラに水やりするで！\n\nほんでこれから10日ごとに水やりしとくわ。ペース変えたいなら教えてな。'
            )
        )
        
    elif text.find('水') != -1 or text.find('みず') != -1:
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                'どの子に水やりしたいん？\n  「エバーフォレスト」\n  「パキラ」'
            )
        )
        
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                '''え、なんて？？ 水やりしたいん？'''
            )
        )

if __name__ == "__main__":
    arg_parser = ArgumentParser(usage = 'Usage: python ' + __file__ + '[--port][--help]')
    arg_parser.add_argument('-p', '--port', default = 8000, help = 'port')
    arg_parser.add_argument('-d', '--debug', default = False, help = 'debug')
    options = arg_parser.parse_args()
    
    app.run(debug = options.debug, port = options.port)