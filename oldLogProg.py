from collections import Counter
import itertools
import datetime
import webhook
import sqlite3
import login
import praw
import time
import json
import os

class Database:
    def __init__(self):
        self.connection = sqlite3.connect(login.data["database"])
        self.cursor = self.connection.cursor()

    def add_action(self, id, mod, action, date, permalink, notes, notes2):
        if id in self.get_ids():
            print("skipped id ", id)
            return
        if permalink is None:
            permalink = ""
        if notes is None:
            notes = ""
        if notes2 is None:
            notes2 = ""
        notes = notes + " " + notes2
        print(mod, action, date, permalink, notes)
        self.cursor.execute("INSERT INTO log (mod, action, date, permalink, notes, id) VALUES (?, ?, ?, ?, ?, ?);", (mod, action, date, permalink, notes, id))
        self.connection.commit()

    def get_ids(self):
        self.cursor.execute("SELECT id FROM log;")
        return [i[0] for i in self.cursor.fetchall()]

def get_actions():
    db = Database()
    actions = {}
    weekactions = {}
    subreddit = login.REDDIT.subreddit(login.data["subredditstream"])
    for mod in subreddit.moderator():
        mod  = str(mod)
        actions[mod] = []
        weekactions[mod] = []
        for log in subreddit.mod.log(mod = mod, limit = None):
            timeago = (time.time() - log.created_utc) / 60 / 60 / 24
            if timeago > 7:
                break
            if timeago <= 1:
                actions[mod].append(log.action)
            weekactions[mod].append(log.action)
            db.add_action(str(log.id), str(log.mod), log.action, int(log.created_utc), log.target_permalink, log.details, log.description)
    return actions, weekactions

def process_actions():
    if not os.path.exists("data.json"):
        actions, weekactions = get_actions()
        if not login.PRODUCTION:
            with open("data.json", "w") as f:
                json.dump(actions, f)
            with open("weekactions.json", "w") as f:
                json.dump(weekactions, f)
    else:
        with open("data.json", 'r') as f:
            actions = json.load(f)
        with open("weekactions.json", "r") as f:
            weekactions = json.load(f)

    discordout = "For a detailed list, click above.```"
    redditout = "\n\n#/r/ComedyHeaven moderator actions"
    discorddata = {}
    for mod in [str(username) for username in login.REDDIT.subreddit(login.data["subredditstream"]).moderator() if str(username) not in ["AutoModerator", "RepostSentinel", "MAGIC_EYE_BOT"]]:
        discorddata[mod] = []
    for i, periodactions in enumerate((actions, weekactions), 0):
        if i == 0:
            redditout += "\n\n##In the last 24h:"
        else:
            redditout += "\n\n##7 day rollover actions:"
        
        #work out actions for each mod
        for mod, actionlist in periodactions.items():
            redditout += "\n\n###%s's actions:\n\nAction|Times Done:\n:--|:--" % mod
            for action, times in Counter(actionlist).items():
                redditout += "\n%s|%s" % (action, times)
            redditout += "\nTotal|%s" % len(actionlist)

        #flat list of all actions
        allactions = list(itertools.chain(*periodactions.values()))
        #length of the longest mod's name. Needed for string formatting later

        #work out number of actions per mod
        redditout += "\n\n###Actions per moderator:\n\nModerator|Times done|Percentage\n:--|:--|:--"
        for mod, actionlist in periodactions.items():
            mod = str(mod)
            if mod not in ["AutoModerator", "RepostSentinel", "MAGIC_EYE_BOT"]:
                discorddata[mod] += [len(actionlist), int((len(actionlist)/len(allactions))*100)]
                redditout += "\n%s|%i|%.2f%%" % (mod, len(actionlist), (len(actionlist)/len(allactions))*100)

        #work out all mod actions
        redditout += "\n\n###All moderators:\n\nAction|Times Done:\n:--|:--"
        for action, times in Counter(allactions).items():
            redditout += "\n%s|%s" % (action, times)
        redditout += "\nTotal|%s" % len(allactions)

    longestusername = max([len(str(username)) for username in login.REDDIT.subreddit(login.data["subredditstream"]).moderator()])
    discordout += "\n%-{0}s %s %s %s %s\n%s".format(longestusername) % ("Moderator", "24h", "24h", "Week", "Week", "-"*(longestusername + 18))

    for mod, data in discorddata.items():
        discordout += "\n%-{0}s %3s %2s%%  %3s %3s%%".format(longestusername) % (mod, data[0], data[1], data[2], data[3])

    discordout += "```\n(Bots aren't included)"

    return redditout, discordout

def send_data(redditout, discordout):
    with open("discord.txt", "w") as f:
        f.write(discordout)
    with open("reddit.txt", "w") as f:
        f.write(redditout)

    title = "/r/ComedyHeaven moderator actions [%s]" % str(datetime.datetime.now())[:10]
    submission = login.REDDIT.subreddit("u_jwnskanzkwk").submit(title, selftext = redditout)
    webhook.send_message("https://redd.it/%s" % submission.id, discordout)

    try:
        submission.mod.sfw()
    except Exception as e:
        print(e)
    try:
        submission.mod.distinguish(sticky = True)
    except Exception as e:
        print(e)

    #if login.PRODUCTION:
    #    login.REDDIT.redditor('emmademontford').message(title, redditout + "\n\nMore details [here.](%s)\n\nThis was done automatically, block this account if you don't like the spam." % submission.url)

def onceaday():
    redditout, discordout = process_actions()
    #send_data(redditout, discordout)

if __name__ == "__main__":
    while True:
        onceaday()
        print("\n\n\n\nProgram executed at %s" % str(datetime.datetime.now()))
        # time.sleep(60 * 60 * 24)

