#!/usr/bin/python
# encoding: utf-8

import requests
import time
import datetime
#import json

whitelist 	= [12345]
admin		= [12345]
base_url = "https://api.telegram.org/<token>/"


ring_stations = [["Ostkreuz", "OX", "OstX"], ["Treptower Park", "TP"],
	["Sonnenallee", "SA"], [u"Neukölln", "NK"], [u"Herrmanstraße", "HS", "Herrmanstr"],
	["Tempelhof", "TH"], [u"Südkreuz", "SX", u"SüdX"], [u"Schöneberg", "SB"],
	["Insbrucker Platz", "IP", "Insbrucker"], ["Bundesplatz", "BP", "Bundes"],
	["Heideberger Platz", "HP", "Heidelberger"], ["Hohenzollerndamm", "HD", "HZD", "Hohenzollern"],
	["Halensee", "HA"], ["Westkreuz", "WX", "WestX"], ["Messe Nord/ ICC", "MN", "ICC", "Messe"],
	["Westend", "WE"], ["Jungfernheide", "JH"], ["Beusselstraße", "BS", "Beusselstr"], ["Westhafen", "WH"],
	["Wedding", "WD"], ["Gesundbrunnen", "GB"], [u"Schönhauser Allee", "SC", u"Schönhauser"],
	["Prenzlauer Allee", "PA", "Prenzlauer"], [u"Greifswalder Straße", "GS", "Greifswalder Str", "Greifswalder"],
	["Landsberger Allee", "LA", "Landsberger"], [u"Storkower Straße", "SS", "Storkower Str", "Storkower"],
	["Frankfurter Allee", "FA", "Frankfurter"]]

def isRingStation(station):
	for s in ring_stations:
		if (station in s):
			return s
	return False
def getStation(from_station, min, direction):
	#times41 = {"TP":2, "SA":3, "NK":2, "HS":1, "TH":4, "SX":3, "SB":2, "IP":1,
	#	"BP":2, "HP":2, "HD":2, "HA":2, "WX":2, "MN":1, "WE":2, "JH":3, "BS":3,
	#	"WH":2, "WD":2, "GB":3, "SC":2, "PA":2, "GS":3, "LA":2, "SS":2, "FA":3, "OX":3}
	#represents time from station at index to the next
	#	times41[0] = time from ring_stations[0] to ring_stations[1], ...
	times = [2,3,2,1,4,3,2,1,2,2,2,2,2,1,2,3,3,2,2,3,2,2,3,2,2,3,3]

	if not isRingStation(from_station):
		return False

	index = 1
	counting = False
	while min > -1:
		#print(index, counting)
		if from_station in ring_stations[index]:
			counting = True
		if counting:
			if direction == "S41": min -= times[index  ]
			else:                  min -= times[index-1]
		if direction == "S41":
			index += 1
			if index >= len(ring_stations): index = 0
		else:
			index -= 1
			if index < 0: index = len(ring_stations) - 1
	return ring_stations[index]

def getMessages(offset):
	data = {"offset": offset}
	response = requests.post(base_url + "getUpdates", data=data)
	return response.json()["result"]
def replyMessage(chat, text, reply_to, force_reply=False, reset_keyboard=True):
	data = {"chat_id": chat, "text": text, "reply_to_message_id": reply_to}
	if force_reply:
		data["reply_markup"] = {"force_reply": True, "selective": True}
	elif reset_keyboard:
		data["reply_markup"] = {"remove_keyboard": True}
	#print(data)
	msg = requests.post(base_url + "sendMessage", json=data).json()
	#print(msg)
	return msg["result"]["message_id"]
#def replyDirection(chat, text, reply_to):
#	data = {"chat_id": chat, "text": text, "reply_to_message_id": reply_to,
#		"reply_markup": {"inline_keyboard": [[{"text": "S41", "callback_data": "S41"}, {"text": "S42", "callback_data": "S42"}]]}}
#	msg = requests.post(base_url + "sendMessage", json=data).json()
#	#print(msg)
#	return msg["result"]["message_id"]
def replyDirection(chat, text, reply_to):
        data = {"chat_id": chat, "text": text, "reply_to_message_id": reply_to,
                "reply_markup": {"keyboard": [[{"text": "S41"}, {"text": "S42"}]], "one_time_keyboard": True, "selective": True}}
        msg = requests.post(base_url + "sendMessage", json=data).json()
        #print(msg)
        return msg["result"]["message_id"]


offset = 0
setLocMsgId = -1
setDirMsgId = -1
lastLoc = False
lastLocTime = False
direction = False
pause = False

while True:
	messages = getMessages(offset)

	for m in messages:
		offset = m["update_id"] + 1
		#
		if not "message" in m:
			print("-"*10)
			print(m)
			continue
		if "new_chat_participant" in m["message"]:
			replyMessage(m["message"]["chat"]["id"], "Hallo " + m["message"]["new_chat_participant"]["first_name"], m["message"]["message_id"])
			continue
#		print(m)

		text = m["message"]["text"].strip()
		chat = m["message"]["chat"]["id"]
		user = m["message"]["from"]["id"]
		msgid= m["message"]["message_id"]
		reply= False
		if ("reply_to_message" in m["message"]):
			reply= m["message"]["reply_to_message"]["message_id"]

		# check auth level
		auth = 0
		if chat in whitelist:
			auth = 1
		if user in admin:
			auth = 2

		# WO
		if text.startswith("/wo"):
			print("wo")
			if lastLoc:
				if pause:
					replyMessage(chat, "Die Gruppe macht hier Pause: " + lastLoc, msgid)
				else:
					min = (datetime.datetime.now() - lastLocTime).seconds / 60
					#replyMessage(chat, "Vor " + str(min) + "min war die Gruppe: " + lastLoc, msgid)
					if direction:
						currentStation = getStation(lastLoc, min, direction)[0]
						replyMessage(chat, "Die Gruppe ist momentan hier: " + currentStation, msgid)
					else:
						replyMessage(chat, "Vor " + str(min) + "war die Gruppe: " + lastLoc +
							u"/nDie aktuelle Position kann nicht berechnet werden, da die Richtung unbekannt ist \U0001f615", msgid)
			else:
				replyMessage(chat, "Standort unbekannt", msgid)
		# GO
		elif auth >= 1 and text.startswith("/go"):
			print("go")
			setLocMsgId = replyMessage(chat, "Aktuelle Station angeben:", msgid, force_reply=True)
		elif auth >= 1 and reply == setLocMsgId:
			if (isRingStation(text)):
				setLocMsgId = -1
				lastLoc = isRingStation(text)[0]
				lastLocTime = datetime.datetime.now()
				print("loc set: " + lastLoc)
				if direction:
					replyMessage(chat, "Station gesetzt: " + lastLoc, msgid)
				else:
					setDirMsgId = replyDirection(chat, "Station gesetzt: " + lastLoc + "\nIn welche Richtung geht es?", msgid)
			else:
				print("loc set fail")
				setLocMsgId = replyMessage(chat, "Diese Station gibt es nicht, versuch es nochmal:", msgid, force_reply=True)
		# DIR
		elif text.startswith("/dir"):
			print("dir")
			if direction:
				replyMessage(chat, "Man fährt mit der " + direction, msgid)
			else:
				replyMessage(chat, "Richtung unbekannt", msgid)
		# SETDIR
		elif auth >= 1 and text.startswith("/setdir"):
			print("setdir")
			setDirMsgId = replyDirection(chat, "Aktuelle Richtung angeben", msgid)
		elif auth >= 1 and reply == setDirMsgId:
			if (text in ("S41", "S42")):
				direction = "S41"
				setDirMsgId = -1
				#replyMessage(chat, text + u", \U0001f44d", msgid, reset_keyboard=True)
				if text == "S41":
					replyMessage(chat, text + u" \u21a9\ufe0f \U0001f44d", msgid, reset_keyboard=True)
				else:
					replyMessage(chat, text + u" \u21aa\ufe0f \U0001f44d", msgid, reset_keyboard=True)
			else:
				setDirMsgId = replyMessage(chat, "Bitte nur 'S41' oder 'S42' eingeben!", msgid, force_reply=True)
		# PAUSE
		elif auth >= 1 and text.startswith("/pause"):
			if not pause:
				pause = True
				min = (datetime.datetime.now() - lastLocTime).seconds / 60
				lastLoc = getStation(lastLoc, min, direction)[0]
				print("pause: " + lastLoc)
				replyMessage(chat, "Es wird pausiert.... (" + lastLoc + ")", msgid)
		# RESUME
		elif auth >= 1 and (text.startswith("/resume") or text.startswith("/weiter")):
			if pause:
				print("resume")
				lastLocTime = datetime.datetime.now()
				pause = False
				replyMessage(chat, "... uuund weiter gehts", msgid)
		# BLOCK GROUP
		elif auth >= 2 and text.startswith("/block_group"):
			print("block: " + str(chat))
			whitelist.remove(chat)
		# WHITELIST GROUP
		elif auth >= 2 and text.startswith("/auth_group"):
			print("auth: " + str(chat))
			whitelist.append(chat)
		# PRINT WHITELIST
		elif auth >= 2 and text.startswith("/whitelist"):
			print(whitelist)
			replyMessage(chat, whitelist, msgid)
		# PRINT USER ID
		elif text.startswith("/userid"):
			print("userid: " + str(user))
			print(m)
			replyMessage(chat, user, msgid)
		# TEST (for emojis, etc)
		elif text.startswith("/test"):
			print(m)

	time.sleep(2)
