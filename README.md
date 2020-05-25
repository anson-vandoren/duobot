# duobot
Duolingo/Telegram bot

To use this bot on your own, you'll need:

- A Telegram bot (and know its token)
  - This is provided by the [BotFather](https://telegram.me/BotFather) when you're creating your bot
- A Telegram group chat set up (and know the chat id)
  - You can easily get this using [this Stackoverflow answer](https://stackoverflow.com/a/32572159/4034665)
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
