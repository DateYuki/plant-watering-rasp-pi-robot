import os
import sys
import threading
from linebot import(LineBotApi, WebhookHandler)
from linebot.exceptions import(InvalidSignatureError)
from linebot.models import(MessageEvent, TextMessage, TextSendMessage,
ButtonsTemplate, PostbackAction, TemplateSendMessage, PostbackEvent)
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
user_id = ''

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
    user_id = event.source.user_id
    if (text.find('今') != -1 or text.find('いま') != -1) or (text.find('水') != -1 or text.find('みず') != -1):
        buttons_template = ButtonsTemplate(
            title = '「今すぐ水やり」を行います。',
            text = 'どちらの植物に水やりしますか？',
            actions = [
                PostbackAction(label = 'エバーフレッシュ', data = 'plant_1_watering'),
                PostbackAction(label = 'パキラ', data = 'plant_2_watering'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「今すぐ水やり」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif (text.find('定期') != -1 or text.find('ていき') != -1) or (text.find('設定') != -1 or text.find('せってい') != -1):
        buttons_template = ButtonsTemplate(
            title = '「定期水やり設定」を行います。',
            text = 'どちらの植物の設定をしますか？',
            actions = [
                PostbackAction(label = 'エバーフレッシュ', data = 'plant_1_setting'),
                PostbackAction(label = 'パキラ', data = 'plant_2_setting'),
                PostbackAction(label = '設定確認', data = 'check_setting'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「定期水やり設定」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                '''よくわかりません。\n「今すぐ水やり」と「定期水やり設定」を行うことができます。'''
            )
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    user_id = event.source.user_id
    if data == 'plant_1_watering':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage('エバーフレッシュに水やりをします。'),
                TextSendMessage('水やりをしています・・・'),
            ]
        )
        plant_water_server.plant1Watering()
        line_bot_api.push_message(
            user_id, [
                TextSendMessage(f'水やりが終了しました。次の水やりは{plant_water_server.plant_1_day_of_interval}日後です。'),
            ]
        )
    elif data == 'plant_2_watering':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage('パキラに水やりをします。'),
                TextSendMessage('水やりをしています・・・'),
            ]
        )
        plant_water_server.plant1Watering()
        line_bot_api.push_message(
            user_id, [
                TextSendMessage(f'水やりが終了しました。次の水やりは{plant_water_server.plant_2_day_of_interval}日後です。'),
            ]
        )
    elif data == 'check_setting':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage('現在の設定を確認しています・・・'),
                TextSendMessage(f'エバーフレッシュへの定期水やり設定は【{plant_water_server.plant_1_day_of_interval}日ごと】に【{plant_water_server.plant_1_water_quantity}ml】です'),
                TextSendMessage(f'パキラへの定期水やり設定は【{plant_water_server.plant_2_day_of_interval}日ごと】に【{plant_water_server.plant_2_water_quantity}ml】です'),
            ]
        )
    elif data == 'plant_1_setting':
        buttons_template = ButtonsTemplate(
            title = '「エバーフレッシュの定期水やり設定」を行います。',
            text = 'どの設定を変更しますか？',
            actions = [
                PostbackAction(label = '間隔', data = 'plant_1_setting_pace'),
                PostbackAction(label = '水量', data = 'plant_1_setting_quantity'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「エバーフレッシュの定期水やり設定」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data == 'plant_1_setting_pace':
        buttons_template = ButtonsTemplate(
            title = '「エバーフレッシュの定期水やり設定-間隔」を行います。',
            text = f'現在の設定は【{plant_water_server.plant_1_day_of_interval}日ごと】です。\n以下の内容から新しい設定を選択してください。',
            actions = [
                PostbackAction(label = '5日ごと', data = 'plant_1_setting_pace_value-5'),
                PostbackAction(label = '7日ごと', data = 'plant_1_setting_pace_value-7'),
                PostbackAction(label = '14日ごと', data = 'plant_1_setting_pace_value-14'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「エバーフレッシュの定期水やり設定-間隔」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data.find('plant_1_setting_pace_value') != -1:
        update_value = int(data[data.indexOf('-'):])
        is_change = plant_water_server.updatePlant1Setting(update_value, plant_water_server.plant_1_water_quantity)
        if (is_change):
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更しました。'),
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更できませんでした。'),
                ]
            )
    elif data == 'plant_1_setting_quantity':
        buttons_template = ButtonsTemplate(
            title = '「エバーフレッシュの定期水やり設定-水量」を行います。',
            text = f'現在の設定は【{plant_water_server.plant_1_water_quantity}ml】です。\n以下の内容から新しい設定を選択してください。',
            actions = [
                PostbackAction(label = '100ml', data = 'plant_1_setting_quantity_value-100'),
                PostbackAction(label = '200ml', data = 'plant_1_setting_quantity_value-200'),
                PostbackAction(label = '400ml', data = 'plant_1_setting_quantity_value-400'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「エバーフレッシュの定期水やり設定-水量」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data.find('plant_1_setting_quantity_value') != -1:
        update_value = int(data[data.indexOf('-'):])
        is_change = plant_water_server.updatePlant1Setting(plant_water_server.plant_1_day_of_interval, update_value)
        if (is_change):
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更しました。'),
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更できませんでした。'),
                ]
            )
    elif data == 'plant_2_setting':
        buttons_template = ButtonsTemplate(
            title = '「パキラの定期水やり設定」を行います。',
            text = 'どの設定を変更しますか？',
            actions = [
                PostbackAction(label = '間隔', data = 'plant_2_setting_pace'),
                PostbackAction(label = '水量', data = 'plant_2_setting_quantity'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「パキラの定期水やり設定」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data == 'plant_2_setting_pace':
        buttons_template = ButtonsTemplate(
            title = '「パキラの定期水やり設定-間隔」を行います。',
            text = f'現在の設定は【{plant_water_server.plant_2_day_of_interval}日ごと】です。\n以下の内容から新しい設定を選択してください。',
            actions = [
                PostbackAction(label = '5日ごと', data = 'plant_2_setting_pace_value-5'),
                PostbackAction(label = '7日ごと', data = 'plant_2_setting_pace_value-7'),
                PostbackAction(label = '14日ごと', data = 'plant_2_setting_pace_value-14'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「パキラの定期水やり設定-間隔」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data.find('plant_2_setting_pace_value') != -1:
        update_value = int(data[data.indexOf('-'):])
        is_change = plant_water_server.updatePlant2Setting(update_value, plant_water_server.plant_2_water_quantity)
        if (is_change):
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更しました。'),
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更できませんでした。'),
                ]
            )
    elif data == 'plant_2_setting_quantity':
        buttons_template = ButtonsTemplate(
            title = '「パキラの定期水やり設定-水量」を行います。',
            text = f'現在の設定は【{plant_water_server.plant_2_water_quantity}ml】です。\n以下の内容から新しい設定を選択してください。',
            actions = [
                PostbackAction(label = '100ml', data = 'plant_2_setting_quantity_value-100'),
                PostbackAction(label = '200ml', data = 'plant_2_setting_quantity_value-200'),
                PostbackAction(label = '400ml', data = 'plant_2_setting_quantity_value-400'),
                PostbackAction(label = 'キャンセル', data = 'cancel'),
            ],
        )
        template_message = TemplateSendMessage(alt_text = '「パキラの定期水やり設定-水量」を行います。', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif data.find('plant_2_setting_quantity_value') != -1:
        update_value = int(data[data.indexOf('-'):])
        is_change = plant_water_server.updatePlant2Setting(plant_water_server.plant_2_day_of_interval, update_value)
        if (is_change):
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更しました。'),
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage('設定を変更できませんでした。'),
                ]
            )
    elif data == 'cancel':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage('キャンセルしました。またお声がけください。'),
            ]
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