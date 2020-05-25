import logging
import os
import random
import sys
import time
from typing import Dict

from duolingo import Duolingo
from telegram import Bot, ParseMode
from dotenv import load_dotenv

load_dotenv()

USER_PATH = os.path.expanduser("~")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=f"{USER_PATH}/duobot.log",
    level=logging.DEBUG,
)

# add convenience type definition
Language = str
Points = int
LangPoints = Dict[Language, Points]


class Friend:
    username: str
    points: int
    languages: LangPoints

    def __init__(self, friend):
        self.username = friend["username"]
        self.points = friend["points"]
        self.languages = {}

    def __str__(self):
        return f"<Friend username: {self.username}, points: {self.points}, languages: {self.languages}"


# add convenience type definition
Friends = Dict[str, Friend]
Username = str
Results = Dict[Username, LangPoints]


def login() -> Duolingo:
    """
    Attempt to log in to Duolingo with username and password from environment
    variables. Exit with error if neither is found, otherwise return the
    Duolingo object
    :return: Duolingo object
    """

    username = os.getenv("DUO_USER", None)
    if username is None:
        logging.error("Cannot start without $DUO_USER set")
        sys.exit("Must set $DUO_USER first")

    password = os.getenv("DUO_PASS", None)
    if password is None:
        print("Must set $DUO_PASS first")
        logging.error("Cannot start without $DUO_PASS set")
        sys.exit("Must set $DUO_PASS first")
    return Duolingo(username, password)


def get_friends(lingo: Duolingo) -> Friends:
    """
    Return a dict of Friends of MAIN_USER, including their total points
    :param lingo: Duolingo object (already logged in)
    :return: dict of Friends, keyed by username
    """

    lingo.set_username(MAIN_USER)
    friends = [Friend(data) for data in lingo.get_friends()]
    for friend in friends:
        logging.debug(f"Found friend: {friend}")
    return {friend.username: friend for friend in friends}


def say_current_points(bot: Bot, friends: Friends) -> None:
    """
    Broadcast language points for all friends to the chat
    :param bot: the Telegram bot
    :param friends: dictionary of friends with current XP
    """

    msg = "Current points:\n"

    for username, friend in friends.items():
        msg += f"\n*{username}*\n"
        for lang, points in friends[username].languages.items():
            msg += f"{lang}: {points}\n"

    bot.send_message(chat_id=CHAT_ID, parse_mode=ParseMode.MARKDOWN, text=msg)


def say_results(bot: Bot, results: Results) -> None:
    """
    Broadcast newly acquired points to the chat
    :param bot: the Telegram bot
    :param results: new changes in XP
    """

    msg = "*Changes detected:*\n"
    for username, changes in results.items():
        msg += "\n"
        for language, delta in changes.items():
            msg += f"{username} gained {delta} points in {language}!\n"
    bot.send_message(chat_id=CHAT_ID, parse_mode=ParseMode.MARKDOWN, text=msg)


def update_points(lingo: Duolingo, friends: Friends) -> None:
    """
    Checks for updates to XP for each language for each friend.
    Updates `friends` dict in place
    :param lingo: logged-in Duolingo object
    :param friends: dict of friends, keyed by username
    """

    for username, friend in friends.items():
        lingo.set_username(username)
        langs = lingo.get_languages()
        for lang in langs:
            points = lingo.get_language_details(lang)["points"]
            friends[username].languages[lang] = points
            logging.debug(f"Found {username} has {points} for {lang}")

    # set back to main user after iterating through all friends
    lingo.set_username(MAIN_USER)


def main():
    lingo = login()

    token = os.getenv("DUO_TOKEN", None)
    if token is None:
        logging.error("$DUO_TOKEN not set - exiting")
        sys.exit("Must set $DUO_TOKEN first")

    # create a Telegram bot from provided token
    bot = Bot(token=token)

    logging.debug("Building XP history for friends")
    friends = get_friends(lingo)
    update_points(lingo, friends)

    logging.debug("Starting polling loop.")

    while True:
        results = poll(lingo, friends)
        if results:
            say_results(bot, results)

        # not sure if they look for API bots, but...
        sleepy_time = random.randint(20, 45)
        logging.debug(f"Sleeping for {sleepy_time} seconds")
        time.sleep(sleepy_time)


def poll(lingo: Duolingo, friends: Friends) -> Results:
    """
    Check if any new XP has been earned for any of `friends`
    :param lingo: logged-in Duolingo object
    :param friends: dict of frneids
    :return: results of any newly earned XP, otherwise empty dict
    """

    results = {}
    new_friends = lingo.get_friends()

    for username, friend in friends.items():
        new_data = [f for f in new_friends if f["username"] == username][0]

        if new_data["points"] == friends[username].points:
            # skip this friend if their total XP hasn't changed since last
            logging.debug(f"No change in total points for {username}... skipping")
            continue
        else:
            # update total XP for this friend
            friends[username].points = new_data["points"]

        # total XP has changed, so check which language has new points
        lingo.set_username(username)
        langs = lingo.get_languages()

        # this friend has some new XP, so add them to return dict
        results[username] = {}

        # find out which languages got more XP
        for lang in langs:
            new_xp = lingo.get_language_details(lang)["points"]
            old_xp = friends[username].languages.get(lang, 0)

            if lang not in friends[username].languages:
                # new language found
                friends[username].languages[lang] = new_xp
                # add this to results since points changed
                results[username][lang] = new_xp
                logging.debug(f"New language '{lang}' for '{username}'")
            elif old_xp < new_xp:
                # known language, but earned new XP
                delta_xp = new_xp - old_xp
                # update results and saved Friend
                results[username][lang] = delta_xp
                friends[username].languages[lang] = new_xp
                logging.debug(f"{username} added points in {lang} by {delta_xp}")

    # restore to the original user
    lingo.set_username(MAIN_USER)
    return results


MAIN_USER = os.getenv("DUO_USER", None)
CHAT_ID = os.getenv("DUO_CHAT_ID", None)
if __name__ == "__main__":
    if MAIN_USER is None:
        sys.exit("$DUO_USER must be set")
    if CHAT_ID is None:
        sys.exit("$DUO_CHAT_ID must be set")

    main()
