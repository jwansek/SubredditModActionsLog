import imgurpython
import json
import praw
import os

PRODUCTION = True
if PRODUCTION and os.path.exists("data.json"):
    os.remove("weekactions.json")
    os.remove("data.json")

with open("credentials.json", "r") as f:
    data = json.load(f)

REDDIT = praw.Reddit(
    client_id = data["redditapi"]["client_id"],
    client_secret = data["redditapi"]["client_secret"],
    username = data["redditapi"]["username"],
    password = data["redditapi"]["password"],
    user_agent = data["redditapi"]["user_agent"],
)

class Discord:
    prodwebhook = data["discordwebhooks"]["prodwebhook"]
    testwebhook = data["discordwebhooks"]["testwebhook"]

IMGUR = imgurpython.ImgurClient(data["imgurapi"]["client_id"], data["imgurapi"]["client_secret"])

DISCORD = Discord()


