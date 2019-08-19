from collections import Counter
from operator import itemgetter
import numpy as np
import matplotlib
import itertools
import datetime
import webhook
import sqlite3
import login
import praw
import time

matplotlib.use('agg')
import matplotlib.pyplot as plt

class Database:
    def __init__(self):
        self.connection = sqlite3.connect("ComedyHeavenModLog.db")
        self.cursor = self.connection.cursor()

    def add_action(self, id, mod, action, date, permalink, notes, notes2):
        if id in self.get_ids():
            print("\tskipped id ", id, "from",  datetime.datetime.fromtimestamp(date))
            return
        if permalink is None:
            permalink = ""
        if notes is None:
            notes = ""
        if notes2 is None:
            notes2 = ""
        notes = notes + " " + notes2
        self.cursor.execute("INSERT INTO log (mod, action, date, permalink, notes, id) VALUES (?, ?, ?, ?, ?, ?);", (mod, action, date, permalink, notes, id))
        print("/u/%-19s %-15s %s %s" % (mod, action, datetime.datetime.fromtimestamp(date), notes))
        self.connection.commit()

    def get_ids(self):
        self.cursor.execute("SELECT id FROM log;")
        return [i[0] for i in self.cursor.fetchall()]

    def get_graph_stats(self):
        self.cursor.execute("SELECT mod, date FROM log;")
        all_actions = self.cursor.fetchall()
        all_actions = self._dates_to_groups([i[1] for i in all_actions if i[0] not in ["AutoModerator", "RepostSentinel", "MAGIC_EYE_BOT"]])
        
        self.cursor.execute("SELECT date FROM log WHERE action = 'removelink';")
        removals = self._dates_to_groups([i[0] for i in self.cursor.fetchall()])
        
        self.cursor.execute("SELECT date FROM log WHERE action = 'approvelink';")
        approvelink = self._dates_to_groups([i[0] for i in self.cursor.fetchall()])

        return {"all_actions": self.reorder_lists(all_actions), "removals": self.reorder_lists(removals), "approvelink": self.reorder_lists(approvelink)}

    def _dates_to_groups(self, dates):
        # convert to datetime, and then to date, count how many values for each unique date and sort by date
        return sorted(Counter([datetime.datetime.utcfromtimestamp(i).date() for i in dates]).items(), key = itemgetter(0))

    def get_filter_toggle(self):
        self.cursor.execute("SELECT DISTINCT date FROM log WHERE action = 'editsettings' AND (notes = 'spam_links ' OR notes = 'spam_selfposts ');")
        return [datetime.datetime.utcfromtimestamp(i[0]) for i in self.cursor.fetchall()]

    def reorder_lists(self, list_):
        """Converts a list of lists into two lists that matplotlib likes"""
        return [[i[0] for i in list_], [i[1] for i in list_]]

    def get_actions(self):
        def get_actions_after(mod, cutoff):
            self.cursor.execute("SELECT mod, action FROM log WHERE date >= ? AND mod = ?;", (cutoff, mod))
            return self.cursor.fetchall()
        
        dailycutoff = time.time() - (60 * 60 * 24)
        weeklycutoff = time.time() - (60 * 60 * 24 * 7)
        dailyactions = {}
        weeklyactions = {}
        for mod in login.REDDIT.subreddit("comedyheaven").moderator():
            mod = str(mod)
            if mod not in ["MAGIC_EYE_BOT", "AutoModerator", "RepostSentinel"]:
                dailyactions[mod] = [i[1] for i in get_actions_after(mod, dailycutoff)]
                weeklyactions[mod] = [i[1] for i in get_actions_after(mod, weeklycutoff)]

        return dailyactions, weeklyactions

def onceaday():
    db = Database()
    start = time.time()
    print("Started at", str(datetime.datetime.now()))
    print("Started loading actions...")
    dailyactions, weeklyactions = db.get_actions()
    print("Finished loading actions.")
    print("Started uploading image...")
    imgururl = upload_image(draw_graph(weeklyactions))
    print("Uploaded graph to %s." % imgururl)

    print("Started processing data...")
    redditout, discordout = process_actions(dailyactions, weeklyactions)
    print("Finished processing data.")

    print("Started posting to reddit...")
    date = str(datetime.date.today())
    submission = login.REDDIT.subreddit("u_jwnskanzkwk").submit("/r/comedyheaven Mod Actions: %s" % date, url = imgururl)
    submission.reply(redditout).mod.distinguish(sticky = True)
    print("Posted to reddit.")

    print("Started posting to discord...")
    webhook.send_message("https://reddit.com" + submission.permalink, discordout, imgururl)
    print("Posted on discord.")

    try:
        submission.mod.sfw()
    except Exception as e:
        print(e)
    try:
        submission.mod.distinguish(sticky = True)
    except Exception as e:
        print(e)
    print("Finished at", str(datetime.datetime.now()), "took", time.time() - start, "seconds.\n")


def process_actions(actions, weekactions):
    discordout = "For a detailed list, click above.```"
    redditout = "\n\n#/r/ComedyHeaven moderator actions"
    discorddata = {}
    for mod in [str(username) for username in login.REDDIT.subreddit("comedyheaven").moderator() if str(username) not in ["AutoModerator", "RepostSentinel", "MAGIC_EYE_BOT"]]:
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

    longestusername = max([len(str(username)) for username in login.REDDIT.subreddit("comedyheaven").moderator()])
    discordout += "\n%-{0}s %s %s  %s %s\n%s".format(longestusername) % ("Moderator", "24h", "24h", "Week", "Week", "-"*(longestusername + 19))

    for mod, data in discorddata.items():
        discordout += "\n%-{0}s %3s %2s%%  %4s %3s%%".format(longestusername) % (mod, data[0], data[1], data[2], data[3])

    discordout += "```\n(Bots aren't included)"

    return redditout, discordout

def get_recent_stats(stats):
    cutoff = datetime.datetime.utcfromtimestamp(time.time() - (60 * 60 * 24 * 7))
    recent_stats = {}
    for type, stat in stats.items():
        for i in stat[0]:
            if datetime.datetime.combine(i, datetime.datetime.min.time()) >= cutoff:
                index = stat[0].index(i)
                break
        recent_stats[type] = [stats[type][0][index:], stats[type][1][index:]]
    return recent_stats, cutoff

def convert_weeklyactions(weeklyactions):
    mods = []
    approvelink = []
    removelink = []
    removecomment = []
    misc = []
    for mod, actions in weeklyactions.items():
        counter = dict(Counter(actions))
        mods.append(mod)
        nonmisc = 0
        if "approvelink" in counter.keys():
            approvelink.append(counter["approvelink"])
            nonmisc += counter["approvelink"]
        else:
            approvelink.append(0)
        if "removelink" in counter.keys():
            removelink.append(counter["removelink"])
            nonmisc += counter["removelink"]
        else:
            removelink.append(0)
        if "removecomment" in counter.keys():
            removecomment.append(counter["removecomment"])
            nonmisc += counter["removecomment"]
        else:
            removecomment.append(0)
        misc.append(len(actions) - nonmisc)
    return mods, approvelink, removelink, removecomment, misc

def draw_graph(weeklyactions):
    db = Database()
    stats = db.get_graph_stats()
    toggle = db.get_filter_toggle()

    recent_stats, cutoff = get_recent_stats(stats)

    mods, approvelink, removelink, removecomment, misc = convert_weeklyactions(weeklyactions)

    fig, (ax0, ax1, ax2) = plt.subplots(nrows = 3)

    ax0.plot(recent_stats["removals"][0], recent_stats["removals"][1], label = "Posts removed", color = "red")
    ax0.plot(recent_stats["approvelink"][0], recent_stats["approvelink"][1], label = "Posts approved", color = "green")
    ax0.plot(recent_stats["all_actions"][0], recent_stats["all_actions"][1], label = "All actions", color = "blue")
    ax0.grid(True)
    ax0.set_facecolor("#E9E9E9")
    ax0.legend(loc = "upper left")

    ax1.plot(stats["removals"][0], stats["removals"][1], label = "Posts removed", color = "red")
    ax1.plot(stats["approvelink"][0], stats["approvelink"][1], label = "Posts approved", color = "green")
    ax1.plot(stats["all_actions"][0], stats["all_actions"][1], label = "All actions", color = "blue")
    ax1.set_facecolor("#E9E9E9")
    ax1.legend(loc = "upper left")


    for time in toggle:
        ax1.axvline(time, color = "orange")
        if time >= cutoff:
            ax0.axvline(time, color = "orange")

    ax2.bar(mods, np.add(np.add(np.add(approvelink, removelink), removecomment), misc), 0.5, color = "green", label = "approvelink")  
    ax2.bar(mods, np.add(np.add(removelink, removecomment), misc), 0.5, color = "red", label = "removelink")
    ax2.bar(mods, np.add(removecomment, misc), 0.5, color = "orange", label = "removecomment")
    ax2.bar(mods, misc, 0.5, color = "gray", label = "misc")
    ax2.xaxis.set_tick_params(rotation = 90)
    ax2.set_facecolor("#E9E9E9")
    ax2.legend(loc = "upper left")
      
    fig.set_size_inches(13, 13)

    filename = "graph.png"
    plt.savefig(filename)
    return filename

def upload_image(path):
    client = login.IMGUR
    date = str(datetime.datetime.now())

    config = {
		'album': None,
		'name':  '/r/comedyheaven statistics graph: %s' % date,
		'title': '/r/comedyheaven statistics graph: %s' % date,
		'description': '/r/comedyheaven statistics graph: %s' % date
    }

    image = client.upload_from_path(path, config = config)

    return "https://i.imgur.com/%s.png" % image["id"]

def stream_actions():
    db = Database()
    subreddit = login.REDDIT.subreddit("comedyheaven")
    for log in praw.models.util.stream_generator(subreddit.mod.log, attribute_name = "id"):
        db.add_action(str(log.id), str(log.mod), log.action, int(log.created_utc), log.target_permalink, log.details, log.description)

if __name__ == "__main__":
    stream_actions()
    #onceaday()
