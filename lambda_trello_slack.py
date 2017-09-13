# -*- coding: utf-8 -*-

import random
import yaml
import sys
import os
import slackweb
from datetime import date,timedelta
from trello import TrelloClient
from collections import OrderedDict
from numpy.random import *

id_list = {}

########
def init2():
	global id_list
	env = os.environ['ENV']
#	env = "DEV"
	today = date.today()
	# dataload
	f = open("data.yaml", "r")
	data = yaml.load(f)
	f.close()
	new_cards = []
	selected_trello_member_names = []
	text_slack = ""

	#inicial
	if env == "PROD":
		trello_member_names = data["prod"]["members"]
		souji_num = len(data["prod"]["souji"])
		client = TrelloClient(api_key=data["prod"]["key"],token=data["prod"]["token"])
		boardname = data["prod"]["boardname"]
		listname = data["prod"]["listname"]
		souji_list = data["prod"]["souji"]
		usermap = data["prod"]["usermap"]
		slack_url = data["prod"]["slack"][0]["url"]
		slack_channel = data["prod"]["slack"][1]["channel"]
		slack_username = data["prod"]["slack"][2]["username"]
		slack_icon_emoji = data["prod"]["slack"][3]["icon_emoji"]
		trellourl = data["prod"]["trellourl"]
		msg1 = data["prod"]["msg1"]
		msg2 = data["prod"]["msg2"]
		msg3 = data["prod"]["msg3"]
	elif env == "DEV":
		trello_member_names = data["dev"]["members"]
		souji_num = len(data["dev"]["souji"])
		client = TrelloClient(api_key=data["dev"]["key"],token=data["dev"]["token"])
		boardname = data["dev"]["boardname"]
		listname = data["dev"]["listname"]
		souji_list = data["dev"]["souji"]
		usermap = data["dev"]["usermap"]
		slack_url = data["dev"]["slack"][0]["url"]
		slack_channel = data["dev"]["slack"][1]["channel"]
		slack_username = data["dev"]["slack"][2]["username"]
		slack_icon_emoji = data["dev"]["slack"][3]["icon_emoji"]
		trellourl = data["dev"]["trellourl"]
		msg1 = data["dev"]["msg1"]
		msg2 = data["dev"]["msg2"]
		msg3 = data["dev"]["msg3"]

	else:
		print("else")

	boards = client.list_boards()
	member_len = len(trello_member_names)

	for board in boards:
		if(board.name == boardname):
			board_all_member_objs = board.all_members()
			lists = board.all_lists()
			for l in lists:
				if(l.name == listname):
					existing_cards = l.list_cards()
					text_slack = create_slack_text_existing_card(existing_cards,usermap,board_all_member_objs,text_slack,msg3)

					existing_souji_names = get_existing_souji_names(existing_cards)
					no_existing_souji_names = list(set(souji_list) - set(existing_souji_names))
					existing_member_names = get_existing_member_names(board_all_member_objs, existing_cards)
					no_existing_trello_member_names = list(set(trello_member_names))
					no_existing_souji_names_len = len(no_existing_souji_names)
					selected_trello_member_names = choice(trello_member_names, no_existing_souji_names_len, replace=False)

					member_ids = get_member_id(board_all_member_objs, selected_trello_member_names)
					member_num = 0

					text_slack = text_slack + '\r\n' + msg1
					for s in no_existing_souji_names:
						#create card
						card = l.add_card(s)
						card.assign(member_ids[member_num])
						card.set_due(today+timedelta(data["dayafter"]))

						#slackpost
						slack_member_name = convert_username_trello_to_slack(usermap,id_list[member_ids[member_num]])
						text_slack = create_slack_text_new_card(slack_member_name, s, text_slack)
						member_num+=1
					text_slack = text_slack + msg2 + trellourl
	slack_post(text_slack, slack_url, slack_channel, slack_username, slack_icon_emoji)
#	print(text_slack)

def create_slack_text_new_card(slack_name,souji_name,text_slack):
	text_slack = text_slack + ' <@' + slack_name + '> : ' + souji_name + '\r\n'
	return text_slack

def create_slack_text_existing_card(existing_cards,usermap,member_objs,text_slack,msg3):
	if(len(existing_cards) > 0):
		text_slack = text_slack + msg3
		for exist_card in existing_cards:
			trello_username = get_member_name(member_objs,exist_card.member_ids[0])
			slack_name = convert_username_trello_to_slack(usermap, trello_username)
			text_slack = text_slack + " <@" + convert_username_trello_to_slack(usermap, trello_username) + "> : " + exist_card.name + "\r\n"
	return text_slack

def convert_username_trello_to_slack(usermap, username):

	for usermap_item in usermap:
		for user_t, user_s in usermap_item.items():
			if(user_t == username):
				return user_s

def get_existing_souji_names(cards):
	souji_names = []
	for card in cards:
		souji_names.append(card.name)
	return souji_names

def get_existing_member_names(member_objs, cards):
	member_names = []
	for card in cards:
		for member_obj in member_objs:
			if(member_obj.id == card.member_ids[0]):
				member_names.append(member_obj.username)
	return member_names

def get_member_name(member_objs, id):
	for member_obj in member_objs:
		if(member_obj.id == id):
			return member_obj.username

def get_member_id(member_objs, names):
	global id_list
	member_ids = []
	for member in member_objs:
		if(member.username in names):
			member_ids.append(member.id)
			id_list[member.id] = member.username
	return member_ids

def slack_post(text_slack, slack_url, slack_channel, slack_username, slack_icon_emoji):
	slack = slackweb.Slack(url=slack_url)
	slack.notify(text=text_slack, channel='#'+slack_channel, username=slack_username, icon_emoji=':'+slack_icon_emoji+':', mrkdwn=True)


def lambda_handler(event, context):
	init2()
	
#init2()


