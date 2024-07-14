import os
import re
import sys
from pathlib import Path

# Set the CWD
current_file_path = Path(__file__).resolve()
cwd = current_file_path.parent.parent.parent
os.chdir(cwd)
sys.path.append(str(cwd))

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.odds_parsing import constants


if __name__ == "__main__":
    rows = list()
    # Parse all categories
    for category in tqdm(constants.CATEGORIES):
        # Get web page information
        url = f"{constants.BASE_URL}/{constants.CATEGORIES[category]}"
        response = requests.get(url)
        while response.status_code != 200:
            response = requests.get(url)

        # Parse data
        soup = BeautifulSoup(response.content, "html.parser")

        # Parse all matches
        matches = soup.find_all("div", class_="betline m-auto betline-wide mb-0")
        for match in matches:
            # Get competitors
            competitors = match.findAll("button", class_="competitor")

            # Get event and bet type
            event, _, bet_type = list(
                match.find("div", class_="flex flex-col ml-2").strings
            )
            event = event.strip()
            bet_type = bet_type.strip()

            team1, team2 = None, None
            team1_odds, team2_odds, draw_odds = None, None, None
            # Parse all competitors
            for competitor in competitors:
                outcome_name = competitor.find(
                    "div", class_="outcome-name"
                ).text.strip()
                outcome_odds = competitor.find(
                    "div", class_="outcome-odds"
                ).text.strip()

                if "right-facing-competitor" in competitor["class"]:
                    team1 = outcome_name
                    team1_odds = outcome_odds
                elif "left-facing-competitor" in competitor["class"]:
                    team2 = outcome_name
                    team2_odds = outcome_odds
                else:
                    draw_odds = outcome_odds

            # Get date
            date = match.find(class_="betline-date-and-props")
            date = date.find("div", class_="text-navy")
            date = date.find("strong").text

            # Format data
            date = re.sub(r"[^a-zA-Z0-9]+", "_", date).lower()
            team1 = re.sub(r"[^a-zA-Z0-9]+", "_", team1).lower()
            team2 = re.sub(r"[^a-zA-Z0-9]+", "_", team2).lower()
            event = re.sub(r"[^a-zA-Z0-9]+", "_", event).lower()
            bet_type = re.sub(r"[^a-zA-Z0-9]+", "_", bet_type).lower()

            # Generate match_id
            match_id = f"{team1}_{team2}_{date}"

            # Append data list of matches
            rows.append(
                (
                    category,
                    match_id,
                    date,
                    team1,
                    team1_odds,
                    team2,
                    team2_odds,
                    draw_odds,
                    event,
                    bet_type,
                )
            )

    df = pd.DataFrame(
        rows,
        columns=[
            "sport",
            "match_id",
            "date",
            "team_1",
            "team_1_odds",
            "team_2",
            "team_2_odds",
            "draw_odds",
            "event",
            "bet_type",
        ],
    )

    df.to_csv("data/data.csv", mode="a", index=False)
