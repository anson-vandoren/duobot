import duolingo
import os
import time
import random
import logging
import sys
from typing import List, Dict
import telegram

userpath = os.path.expanduser("~")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=f"{userpath}/duobot.log",
    level=logging.DEBUG,
)

MAIN_USER = "anson.vandoren"
CHAT_ID = "-406591691"


class Friend:
    username: str
    points: int
    languages: Dict[str, int]

    def __init__(self, friend):
        self.username = friend["username"]
        self.points = friend["points"]
        self.languages = {}

    def __str__(self):
        return f"<Friend username: {self.username}, points: {self.points}, languages: {self.languages}"


def login():
    username = os.getenv("DUO_USER", None)
    password = os.getenv("DUO_PASS", None)
    if username is None:
        print("Must set $DUO_USER first")
        logging.error("Cannot start without $DUO_USER set")
        sys.exit(1)
    if password is None:
        print("Must set $DUO_PASS first")
        logging.error("Cannot start without $DUO_PASS set")
        sys.exit(1)

    return duolingo.Duolingo(username, password)


def get_friends(lingo: duolingo.Duolingo):
    lingo.set_username(MAIN_USER)
    friends = [Friend(data) for data in lingo.get_friends()]
    for friend in friends:
        logging.debug(f"Found friend: {friend}")
    return {friend.username: friend for friend in friends}


def main():
    token = os.getenv("DUO_TOKEN", None)
    if token is None:
        print("Must set $DUO_TOKEN first")
        sys.exit(1)
    bot = telegram.Bot(token=token)
    do_loop(bot)


def bot_current_points(bot: telegram.Bot, friends: Dict[str, Friend]):
    msg = "Current points:\n"
    for username, friend in friends.items():
        msg += f"\n*{username}*\n"
        languages = friends[username].languages
        for language, points in languages.items():
            msg += f"{language}: {points}\n"
    print(msg)
    bot.send_message(chat_id=CHAT_ID, parse_mode=telegram.ParseMode.MARKDOWN, text=msg)


def bot_show_changes(bot: telegram.Bot, results: Dict[str, Dict[str, int]]):
    msg = "*Changes detected:*\n"
    for username, changes in results.items():
        msg += "\n"
        for language, delta in changes.items():
            msg += f"{username} gained {delta} points in {language}!\n"
    bot.send_message(chat_id=CHAT_ID, parse_mode=telegram.ParseMode.MARKDOWN, text=msg)


def do_loop(bot):
    bot.send_message(
        chat_id=CHAT_ID, text="DuoBot coming back online... please wait a moment"
    )
    lingo = login()

    logging.debug("Building XP history for friends")
    friends = get_friends(lingo)
    get_current_points(lingo, friends)

    logging.debug("Starting polling loop.")
    bot_current_points(bot, friends)

    while True:
        results = poll(lingo, friends)
        if results:
            bot_show_changes(bot, results)
        # not sure if they look for API bots, but...
        sleepy_time = random.randint(20, 45)
        logging.debug(f"Sleeping for {sleepy_time} seconds")
        time.sleep(sleepy_time)


def get_current_points(lingo: duolingo.Duolingo, friends: Dict[str, Friend]):
    for username, friend in friends.items():
        lingo.set_username(username)
        languages = lingo.get_languages()
        for language in languages:
            details = lingo.get_language_details(language)
            points = details["points"]
            friends[username].languages[language] = points
            logging.debug(f"Found {username} has {points} for {language}")
    lingo.set_username(MAIN_USER)


def poll(
    lingo: duolingo.Duolingo, friends: Dict[str, Friend]
) -> Dict[str, Dict[str, int]]:
    new_friends = lingo.get_friends()
    results = {}
    for username, friend in friends.items():
        new_data = [f for f in new_friends if f["username"] == username][0]
        if new_data["points"] == friends[username].points:
            logging.debug(f"No change in total points for {username}... skipping")
            continue
        else:
            friends[username].points = new_data["points"]
        lingo.set_username(username)
        languages = lingo.get_languages()
        for language in languages:
            details = lingo.get_language_details(language)
            points = details["points"]
            if language not in friends[username].languages:
                # new language found
                friends[username].languages[language] = points
                logging.debug(
                    f"Found new language '{language}' for friend '{username}'"
                )
                if username not in results:
                    results[username] = {}
                # add this to results since points changed
                results[username][language] = points
            elif friends[username].languages[language] < points:
                if username not in results:
                    results[username] = {}
                results[username][language] = (
                    points - friends[username].languages[language]
                )
                friends[username].languages[language] = points
                logging.debug(
                    f"{username} increased points in {language} by {results[username][language]}"
                )
            else:
                logging.debug(f"{username} kept same points ({points}) in {language}")
    lingo.set_username(MAIN_USER)
    return results


if __name__ == "__main__":
    main()
