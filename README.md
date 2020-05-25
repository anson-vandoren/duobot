# duobot
Duolingo/Telegram bot

To use this bot on your own, you'll need:

- A Telegram bot (and know its token)
- A Telegram group chat set up (and know the chat id)
- A Duolingo account (need to be logged in to access the API)

## Create a .env file

Create a file called `.env` in the folder with the `main.py` script. Add the following, substituting your correct values:

```shell
DUO_USER="myDuolingoUsername"
DUO_PASS="myDuolingoPassword"
DUO_TOKEN="botTokenFromTelegram"
DUO_CHAT_ID="chatIdFromTelegram"
```

Then run `python main.py`
