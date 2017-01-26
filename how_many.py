# Standard imports
import json
import signal
import sys

# Non Standard imports
import requests

# Clase dicctionary

class Dictionary:
	
	def __init__(self):
		self.dicc = {}
		self.top5 = []
		self.cantPalabras = 0

	def agrego_palabra(self,palabra):
		# Transformo todo a minuscula
		palabra = palabra.lower()
		if palabra in self.dicc:
			self.dicc[palabra] = self.dicc[palabra] + 1
		else:
			self.dicc[palabra] = 1
			self.cantPalabras = self.cantPalabras + 1
		# si ya esta en el top 5 actualizo
		apariciones = self.dicc[palabra]
		if (palabra,apariciones-1) in self.top5:
			indice = self.top5.index((palabra,apariciones-1))
			self.top5[indice] = (palabra,apariciones)
		else:
			self.top5.append((palabra,apariciones))
		#ordeno la lista y me quedo con las 5 primeras		
		self.top5.sort(key=lambda tup: tup[1],reverse=True)
		#keep the 5
		if len(self.top5) > 5:
			self.top5.pop(5)

	def show_me_top(self):
		return self.top5

	def how_many(self,palabra):
		if palabra in self.dicc:
			return self.dicc[palabra]
		else:
			return 0

	def cantidad_palabras_diferentes(self):
		return self.cantPalabras	

# Look up for the token in token.in file
try: 
	with open('token.in','r') as file:
		token = file.readline().rstrip('\n')
except IOError:
	print "No encontre el archivo token.in"
else:
	""" Si no encuentra el token nunca define TELEGRAM_URL y se cierra """
	TELEGRAM_URL = "https://api.telegram.org/bot" + token

# Conjunto de palabras a ignorar

ignaradas = set(['y','el','la','los','yo','mi','mis','ellos','ellas','nosotros',',','.','que',' ',"\n"])

def main():
	r = requests.get(TELEGRAM_URL + "/getUpdates",params={'timeout': 0})
	last_update_id = 0
	validjson = True
	"""Diccionario donde guardo para cada chat su historial de palabras"""
	dicc_chat = {}

	try:
		data = json.loads(r.text)
	except ValueError, e:
	    print "Invalid JSON Object, " + str(e)
	    validjson = False
	else:
	    validjson = True

	if validjson and data['ok'] and data['result'] != []:
	        last_update_id = data['result'][-1]['update_id'] + 1

	while True:

		r = requests.get(TELEGRAM_URL+"/getUpdates",params={'offset': last_update_id})
		try:
			data = json.loads(r.text)
		except ValueError, e:
		    print "Invalid JSON Object, " + str(e)
		    validjson = False
		else:
		    validjson = True

		if validjson and data['ok'] and data['result'] != []:
		        last_update_id = data['result'][-1]['update_id'] + 1

	        if not validjson:
	            print "Invalid JSON"
	        elif data['ok'] and data['result'] != []:
	            result = data['result'][0]
	            update_id = result['update_id']

	            if 'message' in result and 'text' in result['message']:
	            	message = result['message']
	                chat_id = message['chat']['id']
	                # si es la primera vez que le escriben al bot agrega el chat al dicc de chats
	                print chat_id
	                if chat_id not in dicc_chat:
	                	dicc_chat[chat_id] = Dictionary() 
	                # print (update_id)
	                
	                try:
	                    print (message['text'])
	                except:
	                    print "Oops, no pude imprimir el texto."
	                
	                if '/showtop' in message['text'].lower():
	                    show_top5(dicc_chat[chat_id],message)

	                elif '/howmany' in message['text'].lower():
	                    how_many(dicc_chat[chat_id],message)

	                elif '/totalwords' in message['text'].lower():
	                	cantidad_palabras(dicc_chat[chat_id],message)

	                else:
	                	agregar_mensaje(dicc_chat[chat_id],message)
	            last_update_id = update_id + 1
	        elif not data['ok']:
	            # Untested!
	            print ('Invalid answer sent!')
	            print ('Error code: ' + str(data['error_code']))
	            print ('Description: ' + data['description'])
	        else:
	            # Timeout, nada que hacer
	            pass

""" Handlers de los comandos"""

def bot_send_msg(chat_id, text):
	"""Realiza un POST al chat_id indicado con el mensaje text."""
	requests.post(
		TELEGRAM_URL + '/sendMessage',
		data={'chat_id': chat_id, 'text': text, 'parse_mode' : 'Markdown'})


def show_top5(dict,message):
	chat_id = message['chat']['id']
	top = dict.show_me_top()
	text = "*Top 5* \n"
	i = 1
	for tupla in top:
		text = text +str(i)+"- "+tupla[0]+": "+str(tupla[1])+"\n"
		i=i+1
	bot_send_msg(chat_id,text)

def how_many(dict,message):
	chat_id = message['chat']['id']
	text = message['text']
	text_split = text.split(' ')
	if len(text_split) > 1:
		#Pasamos la query a minuscula
		query = text_split[1].lower()
		apariciones = dict.how_many(text_split[1])
		msj = "La palabra "+query+" se uso "+ str(apariciones) +" veces."
		bot_send_msg(chat_id,msj)
	else:
		bot_send_msg(chat_id,"ah ah ah you didnt say the magic word!")

def agregar_mensaje(dict,message):
	text = message['text']
	text_split = text.split(' ')
	for string in text_split:
		if string.lower() not in ignaradas:
			dict.agrego_palabra(string)

def cantidad_palabras(dict,message):
	chat_id = message['chat']['id']
	cant_palabras = dict.cantidad_palabras_diferentes()
	msj = "Se usaron "+ str(cant_palabras) +" palabras diferentes hasta el momento."
	bot_send_msg(chat_id,msj)


if __name__ == '__main__':
    main()