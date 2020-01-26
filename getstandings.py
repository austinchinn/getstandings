from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient

urls = ['https://watch.lolesports.com/standings/lcs/lcs_2019_summer/regular_season',
'https://watch.lolesports.com/standings/lec/lec_2019_summer/regular_season']
teams = []

driver = webdriver.Chrome(executable_path='chromedriver.exe')
for url in urls:
	driver.get(url)
	try:
		# Wait for page to load standings
		element = WebDriverWait(driver, 5).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'StandingsList'))
		)
		page = driver.page_source
		soup = BeautifulSoup(page, features='html.parser')

		# Get team placement, name, and record for all teams
		for team in soup.find_all('a', class_='ranking'):
			recordSplit = team.find('div', class_='record').text.split('W-')
			record = recordSplit[0] + " - " + recordSplit[1][:-1]
			
			teams.append({
				'placement': int(team.find('div', class_='ordinal').text),
				'name': team.find('div', class_='name').text,
				'record': record
			})
	except:
		pass

driver.quit()

naTeams = []
euTeams = []
count = 0
currentPlacement = 1
teamsToAdd = []
recordToAdd = ''

for team in teams:
	count += 1

	# If next placement is reached, push the higher placed team(s)
	if(team['placement'] != currentPlacement):
		for i in range(currentPlacement,team['placement']):
			toAdd = {
				'teams':teamsToAdd.copy(),
				'record':recordToAdd
			}
			if(count < 11):
				naTeams.append(toAdd)
			else:
				euTeams.append(toAdd)
		teamsToAdd.clear()
		currentPlacement = team['placement']

	# Add team and record
	teamsToAdd.append(team['name'])
	recordToAdd = team['record']

	# Handle 10th place
	if(count % 10 == 0):
		for i in range(currentPlacement,11):
			toAdd = {
				'teams':teamsToAdd.copy(),
				'record':recordToAdd
			}
			if(count == 10):
				naTeams.append(toAdd)
			else:
				euTeams.append(toAdd)
		teamsToAdd.clear()
		currentPlacement = 1

client = MongoClient('')
db = client['prophet']

collection = db['standings']
collection.update_one({"name":"standings"}, { '$set': {
	'standings': {
		'naTeams': naTeams,
		'euTeams': euTeams
	}} 
})
