#-*- coding: utf-8 -*-
import xmltodict
import os
from sys import argv
import math
from elo import EloRatingSystem
from datetime import datetime
import random

playerLoggingName = [] #debug var
gameCounter = 0 #debug var

class Game:
	def __init__(self, player1, player2, p1CorpScore, p2RunnerScore, p1RunnerScore, p2CorpScore):
		self.player1 = player1
		self.player2 = player2
		self.p1CorpScore = int(p1CorpScore)
		self.p2CorpScore = int(p2CorpScore)
		self.p1RunnerScore = int(p1RunnerScore)
		self.p2RunnerScore = int(p2RunnerScore)
		# if self.p1CorpScore == self.p2RunnerScore or self.p1RunnerScore == self.p2CorpScore:
		# 	print "ERROR: " + player1 + " " + player2

class Player:
	def __init__(self, id, name, corpName, runnerName):
		self.id = id
		self.name = name

		#debug code
		if name == u'Борц Ларик':
			global playerLoggingName
			playerLoggingName.append(id)
		#end debug

		pass
	def __repr__(self):
		return "%s" % (repr(self.name).decode("unicode_escape"))

class Tournament:
	def __init__(self, date, players, rounds, playoff):
		self.date = datetime.strptime(date[:10], '%Y-%m-%d') #2014-02-24T00:00:00+04:00
		self.players = players
		self.rounds = rounds
		self.playoff = playoff
	def __repr__(self):
		return repr("Tournament at %s. Players %i" % (self.date, len(self.players)))


def buildTournamentModel(tournamentDict):
	players = registeredPlayers(tournamentDict["PointsTable"])
	rounds = playedRounds(tournamentDict["Rounds"])
	playoff = playedPlayoffs(tournamentDict["Playoffs"])
	# allGames = rounds + playoff
	tournament = Tournament(tournamentDict["Date"], players, rounds, playoff)
	print "Tournament created: %s" % (tournament)
	return tournament

def registeredPlayers(playersDict):
	players = {}
	for player in playersDict["Player"]:
		players[player["Id"]] = Player(player["Id"], player["Alias"], None, None)
	return players

def parseGame(game):
	player1Id = game["Player1Id"]
	player2Id = game["Player2Id"]
	isBye = game["IsBYE"]
	if isBye == "true":
		return None
	p1Score1 = int(game["Player1Score1"])
	p1Score2 = int(game["Player1Score2"])
	p2Score1 = int(game["Player2Score1"])
	p2Score2 = int(game["Player2Score2"])

	#debug
	if player1Id in playerLoggingName or player2Id in playerLoggingName:
		global gameCounter
		gameCounter += 1
		print "%i %s (%i/%i) - (%i/%i) %s" % (gameCounter, game["Player1Alias"], p1Score1, p1Score2, p2Score1, p2Score2, game["Player2Alias"])
	#end

	if p1Score1 == p2Score1 == 0:
		# print "NULL RESULT " + player1Id + player2Id + repr(game).decode("unicode-escape")
		return None
	if p2Score2 == p1Score2 == 0:
		# print "NULL RESULT " + player1Id + player2Id + repr(game).decode("unicode-escape")
 		return None

	gameObj = Game(player1Id, player2Id, p1Score1, p2Score1, p1Score2, p2Score2)	
	return gameObj

def playedRounds(roundsDict):
	rounds = []
	for round in roundsDict["Round"]:
		games = []
		for game in round["Games"]["Game"]:
			gameObj = parseGame(game)
			if gameObj != None:
				games.append(gameObj)
		rounds.append(games)
	return rounds

def playedPlayoffs(playoffDict):
	playoff = []
	playoffDict.pop("StartRound", None)
	for game in playoffDict.values():
		gameObj = parseGame(game)
		if gameObj != None:
			playoff.append(gameObj)
	return playoff

def calculateRatingsInTournament(tournament, eloRatingSystem):
	def calculateRatingForGame(game):
		p1Name = tournament.players[game.player1].name
		p2Name = tournament.players[game.player2].name
		eloRatingSystem.calculateGame(p1Name, game.p1CorpScore, game.p2RunnerScore, game.p1RunnerScore, game.p2CorpScore, p2Name)
		pass
	for round in tournament.rounds:
		for game in round:
			calculateRatingForGame(game)
	for playoffGame in tournament.playoff:
		calculateRatingForGame(playoffGame)

def loadDataToTournamentsList():
	files = []
	directoryWithLogs = "tournament_logs/"
	for fileName in os.listdir(directoryWithLogs):
		print "Start parse " + fileName
		pathToFile = directoryWithLogs + fileName
		if os.path.isfile(pathToFile):
			file = open(pathToFile)
			xmlString = file.read()
			dict = xmltodict.parse(xmlString)
			files.append(dict)
			file.close()
	tournaments = []
	for dict in files:
		tournament = buildTournamentModel(dict["Tournament"])
		tournaments.append(tournament)
		pass

	tournamentsSortedByDate = sorted(tournaments, key=lambda tournament:tournament.date)
	return tournamentsSortedByDate

def saveListOfStrings(listOfStrings, fileName):
	textTable = '\r\n'.join(listOfStrings)
	# print textTable
	outputFile = open(fileName, 'w')
	outputFile.write(textTable)
	outputFile.close()

def saveHistoryDict(history, folderName):
	for player in history.keys():
		historyString = history[player]
		outputFile = open("%s/%s.txt" % (folderName, player.encode("utf-8")), 'w')
		outputFile.write(historyString.encode("utf-8"))
		outputFile.close()

def executeRatingCalculate():
	tournaments = loadDataToTournamentsList()

	totalPlayers = {}
	eloRatingSystem = EloRatingSystem()
	for tournament in tournaments:
		for player in tournament.players.values():
			counter = 1000
			if player.name in totalPlayers.keys():
				counter = totalPlayers[player.name]
			totalPlayers[player.name] = counter 
		calculateRatingsInTournament(tournament, eloRatingSystem)

	resultTable = eloRatingSystem.ratingTableList()
	saveListOfStrings(resultTable, 'netrunner_elo_rating.csv')
	
	history = eloRatingSystem.historyStringDict()
	saveHistoryDict(history, "playerHistory")

if __name__ == "__main__":
	executeRatingCalculate()