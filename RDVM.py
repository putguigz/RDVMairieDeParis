from concurrent.futures import thread
from genericpath import exists
from lib2to3.pgen2 import driver
from pickle import FALSE
from posixpath import split
from queue import Empty
from threading import local
from tkinter import W
from urllib import request
from webbrowser import BaseBrowser
from datetime import date
from sys import platform
import time
import sys
from signal import signal, SIGINT
from notifypy import Notify
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

""" Chrome_options set up chrome browser to NOT shut down after a slot is found
on the website, and give back control to the user for CAPTCHA INPUT  """
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

BLUE= "\u001b[34;1m"
RESET= "\u001b[0m"
RED= "\u001b[31;1m"
YELLOW= "\u001b[33;1m"
WHITE= "\u001b[37;1m"

""" This is the starting point of any HTTP REQUEST """
calendar_url = "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=getViewAppointmentCalendar&id_form="
form_url = "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=getViewAppointmentForm&id_form="

""" This dictionnary contains all the Mairies-Id as used by the teleservice.paris.fr"""
Mairies = {
	1 : "28",
	2 : "29",
	3 : "29",
	4 : "29",
	5 : "30",
	6 : "31",
	7 : "32",
	8 : "33",
	9 : "34",
	10 : "35",
	11 : "36",
	12 : "37",
	13 : "38",
	14 : "39",
	15 : "40",
	16 : "41",
	17 : "42",
	18 : "43",
	19 : "44",
	20 : "45",
}

def notifyMe():
	""" This is the function managing the notification on user system, 
	MacOS is managed for now """

	notification = Notify()
	notification.title = "RDVMairieDeParis.py"
	notification.message = "Form is waiting for your final input !"
	notification.audio = "./medias/Glass.wav"

	notification.send()

def printparseError():
	""" This Parse error appears if error is detected in the program args """

	print("Mauvais nombre d'arguments.")
	print("La syntaxe est la suivante : python3 RDVMairieDeParis.py <Code Postal> <Date de RDV souhaitée> <Heure de RDV souhaitée>")
	print("Les codes postaux gérés sont ceux compris entre 75001 et 75020. Exemple: 75014")
	print("La Date de RDV est au format JJ/MM/YY. Exemple: 08/12/2022 ou 21/09/2022")
	print("L'heure du RDV est au format HH:MM. Exemple: 8:54 ou 17:30")


def parseArgs(argc, args):
	""" This parse the 1, 2 or 3 args inputed by user """
	if argc == 0:
		return None
	
	new_list = []

	for elem in args:
		if not elem.strip():
			print("Un ou plusieurs arguments sont vides.\nEssayez encore.")
			return None;

		if elem is args[0]:
			if len(elem) != 5:
				print("Le code postal ne peut avoir que 5 chiffres\nEssayez encore.")
				return None
			if elem[:3] != "750":
				print("La syntaxe est du type : <750XX>, XX est votre numero d'arrondissement. Exemple : '75019' ou '75001'\nEssayez encore.")
				return None
			if elem == "75000" and argc < 2:
				print("Ajoutez une date pour le mode multi-mairie.")
				return None
			if int(elem[3:]) < 0 or int(elem[3:]) > 20:
				print("Le numéro d'arrondissement doit être compris entre 0 et 20.\nEssayez encore.")
				return None
			else:
				new_list.append(int(elem[3:]))
			if argc == 1:
				return new_list
			else:
				continue

		if elem is args[1]:
			today = date.today()
			d3 = today.strftime("%d/%m/%Y")
			current_date = d3.rsplit('/')
			input_date = elem.rsplit('/')
			if len(input_date) != 3:
				print("La date doit etre composée d'1 jour, d'1 mois et d'1 année. Exemple : '28/03/2022', '4/9/2022'")
				return None
			if int(input_date[0]) > 31 or int(input_date[0]) < 1:
				print("Choisissez un jour compris entre le 1 et le 31.")	
				return None
			elif int(input_date[1]) > 12 or int(input_date[1]) < 1:
				print("Choisissez un mois compris entre janvier et Décembre (1 à 12)")
				return None
			elif int(input_date[2]) < int(current_date[2]):
				print("N'essayez pas de prendre un RDV dans le passé !")
				return None
			elif int(input_date[2]) == int(current_date[2]) and int(input_date[1]) <= int(current_date[1]):
				if int(input_date[1]) < int(current_date[1]):
					print("N'essayez pas de prendre un RDV dans le passé !")
					return None
				if int(input_date[1]) == int(current_date[1]) and int(input_date[0]) < int(current_date[0]):
					print("N'essayez pas de prendre un RDV dans le passé !")
					return None
			formated_elem = (input_date[0].rjust(2, '0'), input_date[1].rjust(2, '0'), input_date[2])
			new_list.append(formated_elem)
			if argc == 2:
				return new_list
			else:
				continue

		if elem is args[2]:
			splited = elem.partition(":")
			if not splited[1] and not splited[2] or int(splited[0]) > 19 or int(splited[0]) < 8 \
			or int(splited[2]) < 0 or int(splited[2]) > 59 \
			or (int(splited[0]) == 19 and int(splited[2]) > 0) \
			or (int(splited[0]) == 8 and int(splited[2]) < 30):
				print("La syntaxe est du type <HH:MM>. Choisissez un créneau entre 8h30 et 19h00. Exemple : '08:45' ou '17:30'.")
				return None
			else:
				new_list.append((splited[0], splited[2]))
	return new_list

def getKey(nb):
	""" This function return a str needed to access field in dictionnary 
	created earlier on user input """

	if nb == 0:
		return ("nom")
	elif nb == 1:
		return ("prenom")
	elif nb == 2:
		return ("email")
	elif nb == 3:
		return ("email")
	elif nb == 4:
		return ("telephone")
	elif nb == 5:
		return ("code postal")

def fillForm(browser):
	""" This function fill the fields of a page using XPATH to navigate from 
	case to case, using what the user gave in stdin earlier """

	fields = browser.find_elements(By.CLASS_NAME, "form-control")
	counter = 0
	for elem in fields:
		elem.send_keys(inputs[getKey(counter)])
		counter += 1
	tmp = browser.find_element(By.XPATH, '//*[@id="form-validate"]/div/div[3]/div/div/button')
	tmp.click()


def bookAnySlot(arrond, refresh=True):
	""" This function books any slot for a given Mairie, 
	using detection of calendar class, which appears if at least ONE slot is available.
	So this function while loop as long as calendar elem is not detected, 
	then may proceed """

	request_url = calendar_url + Mairies[arrond]
	browser.get(request_url)
	timer = WebDriverWait(browser, 2)
	while True:
		try:
			timer.until(EC.presence_of_all_elements_located((By.ID, "calendar")))
		except Exception:
			if refresh is False:
				return 0
			browser.refresh()
		else:
			content = browser.find_element(by=By.CSS_SELECTOR, value="a[class='fc-day-grid-event fc-h-event fc-event fc-start fc-end ']")
			browser.get(content.get_attribute("href"))
			fillForm(browser)
			notifyMe()
			return 1

def scanMairies():
	while True:
		for i in range(len(Mairies)):
			if (i + 1) == 3 or (i + 1) == 4:
				continue
			if bookAnySlot(i + 1, refresh=False):
				return

def bookSlot(url,refresh=True):
	browser.get(url)
	timer = WebDriverWait(browser, 2)
	while True:
		try:
			timer.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "form-control")))
		except Exception:
			if refresh is False:
				return 0
			browser.refresh()
		else:
			fillForm(browser)
			Notify()
			return 1
	return

def quarterFix(startHour, minutes):
	if (minutes % 15 == 0):
		return startHour, minutes
	else:
		quarts = []
		idx = 0
		while idx != 75:
			quarts.append(idx)
			idx += 15
		shortest_span = 60
		for elem in quarts:
			dist = abs(minutes - elem)
			if dist < shortest_span:
				if shortest_span != 60:
					shortest_span = elem
				else:
					shortest_span = 0
					if startHour != 19:
						startHour += 1
		return startHour, shortest_span


def bookWantedHour(args):

	main_url = form_url + Mairies[args[0]]
	date_of_rdv = "&starting_date_time=" + args[1][2] + '-' + args[1][1] + '-' + args[1][0]
	main_url += date_of_rdv
	trailer_url = "&modif_date=false&anchor=step3"
	while True:
		ret = quarterFix(int(args[2][0]), int(args[2][1]))
		startHour = ret[0]
		startMins = ret[1]
		Hour = startHour
		Mins = startMins
		for i in range(4):
			hour_url = 'T' + (str(Hour)).rjust(2, '0') + ':' + str(Mins).rjust(2, '0')
			tmp_url = main_url + hour_url + trailer_url
			if bookSlot(tmp_url, False):
				return
			Mins += 15
			if Mins == 60:
				Hour += 1
				Mins = 0
			if Hour == 19 and Mins == 15:
				break
			elif Hour == startHour + 1 and Mins == startMins:
				break
	return
		


def	bookWantedDay(args, loop=True):
	""" This function find a Mairie and a day and iter through all hour of the day until an open slot is found """
	
	## FORMAT == https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointment&view=getViewAppointmentCalendar&id_form=35&starting_date_time=2022-03-22T09:00&modif_date=false&anchor=step3 ##
	main_url = form_url + Mairies[args[0]]
	date_of_rdv = "&starting_date_time=" + args[1][2] + '-' + args[1][1] + '-' + args[1][0]
	main_url += date_of_rdv
	trailer_url = "&modif_date=false&anchor=step3"
	end = True;
	while end:
		Hour = 8
		while Hour != 20:
			if Hour == 8:
				Mins = 30
			else:
				Mins = 0
			while Mins != 60:
				hour_url = 'T' + (str(Hour)).rjust(2, '0') + ':' + str(Mins).rjust(2, '0')
				tmp_url = main_url + hour_url + trailer_url
				if bookSlot(tmp_url, False):
					return True
				Mins += 15
				if Hour == 19 and Mins == 15:
					break
			Hour += 1
		if loop is False:
			end = False
	return False

def loopMairieonDay(args):
	while True:
		args[0] = 1
		while (args[0] != 20):
			if bookWantedDay(args, loop=False):
				return
			if (args[0] == 2):
				args[0] += 3
			else:
				args[0] += 1

def getInput():
	""" This function request user input for form completion and store it in a 
	dictionnary. Parsing may be requested to avoid numerical input in first and 
	lastaname, then showing input to user, and asking him if ok or if redo 
	is necessary """

	are_you_happy = False
	new_dico = {}
	
	print(f"RDV {BLUE}Mairie{RESET} {WHITE}de{RESET} {RED}Paris{RESET}")
	while not are_you_happy:
		new_dico["prenom"] = input("Entrez votre prénom: ").strip()
		new_dico["nom"] = input("Entrez votre nom de famille: ").strip()
		new_dico["email"] = input("Entrez votre e-mail: ").strip()
		new_dico["telephone"] = input("Entrez votre numéro de téléphone (10 chiffres): ").strip()
		new_dico["code postal"] = input("Entrez votre code postal (Tapez 99999 si vous résidez à l'étranger.) : ").strip()
		print()
		""" Imprimer input """
		for key, word in new_dico.items():
				print(key, word, sep=" : ")
		while True:
			resp = input("Êtes-vous satisfait par vos informations ? Tapez 'oui' ou 'non' : ")
			if resp.strip() == "oui":
				are_you_happy = True;
				break
			elif resp.strip() == "non":
				print("Essayons encore !")
				new_dico.clear()
				break
			else:
				print("Je n'ai pas compris votre réponse.")
	return new_dico

def sigint_handler(sig, frame):
	print(f"{YELLOW}Fin du Programme. A bientot en Mairie !{RESET}")
	if "browser" in locals():
		browser.quit()
	exit(0)

if __name__ == "__main__":

	signal(SIGINT, sigint_handler)

	argc = len(sys.argv) - 1
	if argc > 3:
		printparseError()
	else:
		args = parseArgs(argc, sys.argv[1:])
	if not args and argc != 0:
		exit()
	inputs = getInput()
	""" ARGC == 0 ---> program look for first available slot in any Mairie 
		ARGC == 1 ---> program look for specified Mairie and refresh until it gets a slot
		ARGC == 2 ---> program look for specified Mairie at specified day, until it finds a slot looping through all hours
		ARGS == 3 ---> program look for specified Mairie at specified day, at specified time -+30 min, until it finds a slot
	""" 
	service = ChromeService(executable_path=ChromeDriverManager().install())
	browser = webdriver.Chrome(service=service, options=chrome_options)
	if argc == 0:
		scanMairies()
	elif argc == 1:
		bookAnySlot(args[0])
	elif argc == 2 and args[0] == 0:
		loopMairieonDay(args)
	elif argc == 2:
		bookWantedDay(args)
	else:
		bookWantedHour(args)
	exit(0)
