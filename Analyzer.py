import requests
import pandas as pd
import matplotlib.pyplot as plt

class PUBGPlayerAnalyzer:
    def __init__(self, api_key):
        self.API_URL = "https://api.pubg.com/shards/steam"
        self.HEADERS = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json"
        }

    def getPlayerId(self, playerName):
        response = requests.get(f"{self.API_URL}/players?filter[playerNames]={playerName}", headers=self.HEADERS)
        if response.status_code == 200:
            data = response.json()
            return data["data"][0]["id"]
        else:
            print("Failed to fetch player ID:", response.status_code, response.json())
            return None

    def getMatchIds(self, playerId):
        response = requests.get(f"{self.API_URL}/players/{playerId}", headers=self.HEADERS)
        if response.status_code == 200:
            data = response.json()
            match_ids = [match["id"] for match in data["data"]["relationships"]["matches"]["data"]]
            return match_ids
        else:
            print("Failed to fetch match IDs:", response.status_code, response.json())
            return []

    def getMatchDetail(self, matchId):
        response = requests.get(f"{self.API_URL}/matches/{matchId}", headers=self.HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch match details:", response.status_code, response.json())
            return None

    def collectPlayerStats(self, playerId, matchData):
        statsList = []
        for participant in matchData["included"]:
            if participant["type"] == "participant" and participant["attributes"]["stats"]["playerId"] == playerId:
                stats = participant["attributes"]["stats"]
                match_stats = {
                    "match_id": matchData["data"]["id"],
                    "kills": stats.get("kills", 0),
                    "damageDealt": stats.get("damageDealt", 0),
                    "timeSurvived": stats.get("timeSurvived", 0),
                    "rank": stats.get("winPlace", 0)
                }
                statsList.append(match_stats)
        return statsList

    def getPlayerData(self, playerName):
        player_id = self.getPlayerId(playerName)
        if not player_id:
            return pd.DataFrame() 

        match_ids = self.getMatchIds(player_id)
        all_stats = []
        for match_id in match_ids:
            match_data = self.getMatchDetail(match_id)
            if match_data:
                match_stats = self.collectPlayerStats(player_id, match_data)
                all_stats.extend(match_stats)

        return pd.DataFrame(all_stats)

    def classifyPlaystyle(self, playerData):

        aggressive_threshold = playerData["kills"].quantile(0.75)
        passive_threshold = playerData["kills"].quantile(0.25)

        def determine_style(row):
            if row["kills"] >= aggressive_threshold and row["damageDealt"] > 500:
                return "Aggressive"
            elif row["kills"] <= passive_threshold and row["timeSurvived"] >= 1200:
                return "Passive"
            return "Balanced"

        playerData["playstyle"] = playerData.apply(determine_style, axis=1)
        return playerData

    def plotPlaystyleSummary(self, playerData):
        playstyle_summary = playerData["playstyle"].value_counts()
        playstyle_summary.plot(kind="bar", color=["skyblue", "salmon", "lightgreen"])
        plt.title("Playstyle Summary")
        plt.xlabel("Playstyle")
        plt.ylabel("Number of Matches")
        plt.show()

    def analyzePlayer(self, playerName):

        player_data = self.getPlayerData(playerName)
        if player_data.empty:
            print(f"No data available for player: {playerName}")
            return

      
        player_data_classified = self.classifyPlaystyle(player_data)
        self.plotPlaystyleSummary(player_data_classified)

       
        return player_data_classified

    def calculateTop10WinRateByPlaystyle(self, playerData):

        top10_data = playerData[playerData["rank"] <= 10]


        playstyle_summary = top10_data.groupby("playstyle").agg(
            top10_matches=("rank", "size"),     
            top10_wins=("rank", lambda x: (x == 1).sum()) 
        )


        playstyle_summary["top10_win_rate"] = playstyle_summary["top10_wins"] / playstyle_summary["top10_matches"]

        return playstyle_summary[["top10_matches", "top10_wins", "top10_win_rate"]]

    def printHighestWinRatePlaystyle(self, playerData, playerName):
 
        top10_win_rate_summary = self.calculateTop10WinRateByPlaystyle(playerData)


        highest_win_rate_playstyle = top10_win_rate_summary["top10_win_rate"].idxmax()
        highest_win_rate = top10_win_rate_summary["top10_win_rate"].max()

        print(f"Player: {playerName}")
        print(f"Highest Win Rate Playstyle: {highest_win_rate_playstyle}")
        print(f"Win Rate: {highest_win_rate:.2%}")

api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI0MGY2Mzg1MC02YzM0LTAxM2QtNDRjNC0xNjVmNmJlZjNhYmMiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzI4ODk0NTI2LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6InB1Ymdfc3Vydml2YWxfIn0.evM3arqRlKF9j8o3nIyq-lTedu3k0FtS1Yy1gdB_-ck"  # Replace with your actual PUBG API key
