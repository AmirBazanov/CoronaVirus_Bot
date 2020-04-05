import telebot
from telebot import types
from telebot.types import Message
import covid
from translate import Translator
import requests

TOKEN = 'TOKEN'
translate = Translator(to_lang='en', from_lang='ru')
covid = covid.Covid()
bot = telebot.TeleBot(TOKEN)
alias = {'worldwide': 'world', 'usa': 'us', 'america': 'us',
         'england': 'united kingdom', 'check republic': 'czechia',
         'africa': 'central african republic', 'arab emirates': 'united arab emirates'}
all_country = [i['name'].lower() for i in covid.list_countries()]


@bot.message_handler(commands=['start', 'help'])
def start(message: Message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
	btn1 = types.KeyboardButton('Во всём мире🌎')
	btn2 = types.KeyboardButton('Украина🇺🇦')
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
	if '🌎' in def_name or '🇺🇦' in def_name or '🇷🇺' in def_name or '🇺🇿' in def_name:
		def_name = def_name[:-2]
		country = translate.translate(def_name).lower()
	if country in alias.keys():
		country = alias[country]
	if country[0] == def_name[0].lower() and len(def_name) < len(country):
		country = country[len(def_name) + 2:-1]
	try:
		get_population = requests.get(f'https://coronavirus-tracker-api.herokuapp.com/v2/locations?country={country}&source=jhu')
		population = get_population.json()['locations'][0]['country_population']
		send_stat = covid.get_status_by_country_name(country)
		bot.send_message(message.chat.id, f"<b><u>🇲🇶{def_name}🇲🇶:</u></b>\n"
		                                  f"<i>🧍Население🧍: </i>{population}\n"
		                                  f"<i>🦠Больных🦠: </i>{send_stat['confirmed']}\n"
		                                  f"<i>💀Умерших💀: </i>{send_stat['deaths']}\n"
		                                  f"<i>💉Выздоровевших💉: </i>{send_stat['recovered']}", parse_mode='html')
		print('Searched: ' + country + " User " + message.from_user.first_name + " " + message.from_user.last_name)
	except KeyError or ValueError:
		if country == 'world':
			bot.send_message(message.chat.id, f'<u><b>🗺️В мире🗺️:</b></u>\n'
			                                  f"<i>🧍Население🧍: </i>7383008820\n"
			                                  f'<i>🦠Больных🦠: </i>{covid.get_total_confirmed_cases()}\n'
			                                  f'<i>💀Умерших💀: </i>{covid.get_total_deaths()}\n'
			                                  f'<i>💉Выздоровевших💉: </i>{covid.get_total_recovered()}',
			                 parse_mode='html')
		else:
			print('Error name ' + country + ' User Name ' + message.from_user.first_name + " " + message.from_user.last_name)
			bot.send_message(message.chat.id, f"<b>❌Страны {def_name} не существует❌</b>",
			                 parse_mode='html')


@bot.inline_handler(lambda query: True)
def query_text(query: types.InlineQuery):
	translated = translate.translate(query.query).lower()
	if translated in alias.keys():
		translated = alias[translated]
	if translated in all_country:
		send_stat = covid.get_status_by_country_name(translated)
	else:
		send_stat = None
	try:
		get_population = requests.get(
			f'https://coronavirus-tracker-api.herokuapp.com/v2/locations?country={translated}&source=jhu')
		population = get_population.json()['locations'][0]['country_population']
		world = types.InlineQueryResultArticle('1', "Мир", types.InputTextMessageContent(
			f'<u><b>🗺️В мире🗺️:</b></u>\n'
			f"<i>🧍Население🧍: </i>7383008820\n"
			f'<i>🦠Больных🦠: </i>{covid.get_total_confirmed_cases()}\n'
			f'<i>💀Умерших💀: </i>{covid.get_total_deaths()}\n'
			f'<i>💉Выздоровевших💉: </i>{covid.get_total_recovered()}',
			parse_mode='html'))
		country = types.InlineQueryResultArticle('2', query.query.title(), types.InputTextMessageContent(
			f"<b><u>🇲🇶{query.query}🇲🇶:</u></b>\n"
			f"<i>🧍Население🧍: </i>{population}\n"
			f"<i>🦠Больных🦠: </i>{send_stat['confirmed']}\n"
			f"<i>💀Умерших💀: </i>{send_stat['deaths']}\n"
			f"<i>💉Выздоровевших💉: </i>{send_stat['recovered']}", parse_mode='html'))
		bot.answer_inline_query(query.id, [world, country])
	except Exception or KeyError or ValueError as e:
		bot.answer_inline_query(query.id, [
				types.InlineQueryResultArticle('1', "Мир",
				                               types.InputTextMessageContent(
					                               f'<u><b>🗺️В мире🗺️:</b></u>\n'
					                               f"<i>🧍Население🧍: </i>7383008820\n"
					                               f'<i>🦠Больных🦠: </i>{covid.get_total_confirmed_cases()}\n '
					                               f'<i>💀Умерших💀: </i>{covid.get_total_deaths()}\n'
					                               f'<i>💉Выздоровевших💉: </i>{covid.get_total_recovered()}',
					                               parse_mode='html')),
				types.InlineQueryResultArticle('2', f'{query.query} странны нету',
				                               types.InputTextMessageContent(
					                               f'<b>Cтраны {query.query} нету</b>', parse_mode='html'))])
		
		print("Inline Error: " + str(e))


bot.polling(none_stop=True, timeout=60)
