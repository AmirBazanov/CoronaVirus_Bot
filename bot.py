import telebot
from telebot import types
from telebot.types import Message
import covid
from translate import Translator
from flask import Flask, request
from flask_sslify import SSLify
import os


server = Flask(__name__)
sslify = SSLify(server)
translate = Translator(to_lang='en', from_lang='ru')
covid = covid.Covid()
TOKEN = '918361897:AAFaWodgWzVYMnAUZNLP6O4g8YBzs2rbhNA'
bot = telebot.TeleBot(TOKEN)

alias = {'worldwide': 'world', 'usa': 'us', 'america': 'us',
         'england': 'united kingdom', 'check republic': 'czechia',
         'africa': 'central african republic', 'arab emirates': 'united arab emirates', 'usd': 'us',
         "united states": 'us'}
all_country = [i['name'].lower() for i in covid.list_countries()]


@bot.message_handler(commands=['start', 'help'])
def start(message: Message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
	btn1 = types.KeyboardButton('Во всём мире🌎')
	btn2 = types.KeyboardButton('США🇺🇸')
	btn3 = types.KeyboardButton('Россия🇷🇺')
	btn4 = types.KeyboardButton('Узбекистан🇺🇿')
	markup.add(btn1, btn2, btn3, btn4)

	send_message = f"<b>Привет {message.from_user.first_name}!</b>\n" \
	               f"Чтобы узнать данные про коронавирус напишите\n" \
	               f"название страны, например: США, Украина, Россия и так далее\n" \
	               f"Вы так же можете использовать бота в других чатах (Инлайн)," \
	               f"просто введите \n" \
	               f"@{bot.get_me().username}\n" \
	               f"⚠️<b>Бот не является врачом не пытайтесь консультироваться с ним</b>⚠️"
	bot.send_message(message.chat.id, send_message, parse_mode='html', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def sendInfo(message: Message):
	def_name = str(message.text).title()
	country = translate.translate(def_name).lower()
	if '🌎' in def_name or "🇺🇸" in def_name or '🇷🇺' in def_name or '🇺🇿' in def_name:
		def_name = def_name[:-2]
		country = translate.translate(def_name).lower()
		print(country)
	if country in alias.keys():
		country = alias[country]
	if country[0] == def_name[0].lower() and len(def_name) < len(country):
		country = country[len(def_name) + 2:-1]
	try:
		if country in all_country:
			print('Searched: ' + country + " User " + str(message.from_user.first_name) + " " + str(
				message.from_user.last_name))
		send_stat = covid.get_status_by_country_name(country)
		bot.send_message(message.chat.id, f"<b><u>🇲🇶{def_name}🇲🇶:</u></b>\n"
		                                  f"<i>🦠Больных🦠: </i>{send_stat['confirmed']}\n"
		                                  f"<i>💀Умерших💀: </i>{send_stat['deaths']}\n"
		                                  f"<i>💉Выздоровевших💉: </i>{send_stat['recovered']}", parse_mode='html')
	except ValueError or KeyError:
		if country == 'world':
			bot.send_message(message.chat.id, f'<u><b>🗺️В мире🗺️:</b></u>\n'
			                                  f'<i>🦠Больных🦠: </i>{covid.get_total_confirmed_cases()}\n'
			                                  f'<i>💀Умерших💀: </i>{covid.get_total_deaths()}\n'
			                                  f'<i>💉Выздоровевших💉: </i>{covid.get_total_recovered()}',
			                 parse_mode='html')
		else:
			print(
				'Error name ' + country + ' User Name ' + str(message.from_user.first_name) + " " + str(
					message.from_user.last_name))
			bot.send_message(message.chat.id, f"<b>❌Страны {def_name} не существует❌</b>",
			                 parse_mode='html')


@bot.inline_handler(lambda query: 10 > 0)
def query_text(query: types.InlineQuery):
	translated = translate.translate(query.query).lower()
	if translated in alias.keys():
		translated = alias[translated]
	if translated in all_country:
		send_stat = covid.get_status_by_country_name(translated)
	else:
		send_stat = {'confirmed': "wrong"}
	try:
		world = types.InlineQueryResultArticle('1', "Мир", types.InputTextMessageContent(
			f'<u><b>🗺️В мире🗺️:</b></u>\n'
			f'<i>🦠Больных🦠: </i>{covid.get_total_confirmed_cases()}\n'
			f'<i>💀Умерших💀: </i>{covid.get_total_deaths()}\n'
			f'<i>💉Выздоровевших💉: </i>{covid.get_total_recovered()}',
			parse_mode='html'))
		country = types.InlineQueryResultArticle('2', query.query.title(), types.InputTextMessageContent(
			f"<b><u>🇲🇶{query.query}🇲🇶:</u></b>\n"
			f"<i>🦠Больных🦠: </i>{send_stat['confirmed']}\n"
			f"<i>💀Умерших💀: </i>{send_stat['deaths']}\n"
			f"<i>💉Выздоровевших💉: </i>{send_stat['recovered']}"
			if send_stat['confirmed'] != 'wrong' else f"<b>❌Такой страны не существует❌</b>", parse_mode='html'))
		bot.answer_inline_query(query.id, [world, country if send_stat['confirmed'] != 'wrong'
		else types.InlineQueryResultArticle('2', f'{query.query} странны нету',
		                                    types.InputTextMessageContent(f'<b>Cтраны {query.query} нету</b>',
		                                                                  parse_mode='html'))])
	except Exception as e:
		print(str(e) + " Inline Error ")


@server.route("/" + TOKEN, methods=["POST"])
def getMessage():
	for i in [telebot.types.Update.de_json(request.get_json())]:
		print(i)
	bot.process_new_updates([telebot.types.Update.de_json(request.get_json())])
	return "!", 200


@server.route("/")
def web_hook():
	bot.remove_webhook()
	bot.set_webhook(url='https://coronavirusbotam.herokuapp.com/' + TOKEN)
	return "!", 200


if __name__ == "__main__":
	server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
