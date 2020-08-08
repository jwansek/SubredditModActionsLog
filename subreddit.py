import numpy as np
import database
import datetime
import praw
import time

REDDIT = praw.Reddit(**database.CONFIG["redditapi"])

def get_mods(subreddit, db):
    return [
        i for i in REDDIT.subreddit(subreddit).moderator() 
        if str(i) not in db.get_bots(subreddit)
    ]
    
def format_actions_reddit(db, subreddit, since = None, vertical = False):
    outobj = {}
    mods = get_mods(subreddit, db)
    grand_total = 0

    #first of all we need to add zeros where there are no actions.
    #but we don't know the actions at this point, so this isn't
    #trivial. We use a dictionary:
    for c, mod in enumerate(mods, 0):       
        action_names_dealt_with = set()
        for action_name, times in db.get_actions(subreddit, mod, since):
            action_names_dealt_with.add(action_name)
            grand_total += times
            
            if action_name not in outobj.keys():
                # if its a new action, add a new key add pad value with zeros
                outobj[action_name] = [0 for i in range(c)] + [times]
            else:
                outobj[action_name].append(times)

        #if there's an action we haven't come across, add a zero for it
        for undeltwith_action_name in set(outobj.keys()) - action_names_dealt_with:
            outobj[undeltwith_action_name].append(0)

    outtable = [[r"Action\Moderator"] + [str(mod) for mod in mods] + ["Total"]]
    for k, v in outobj.items():
        outtable.append([k] + v + ["%i (%.1f%%)" % (sum(v), (sum(v) / grand_total) * 100)])

    outtable = np.array(outtable)
    sums = list(np.sum(np.array(outtable[1:, 1:-1], dtype = int), axis = 0))
    outtable = np.vstack([
        outtable, 
        ["Total"] + 
        ["%i (%.1f%%)" % (sum_, (sum_ / grand_total) * 100) for sum_ in sums] + 
        [grand_total]
    ])

    #if vertical is True, mods will be on the side and actions will be at the top
    if vertical:
        outtable = np.fliplr(np.rot90(outtable, k=3))
        outtable[0][0] = r"Moderator\Action"

    outstr = ""
    for c, row in enumerate(outtable, 1):
        if c == 1 or c == len(outtable):
            outstr += "**%s**\n" % "**|**".join(row)
            if c == 1:
                outstr += ":--%s\n" % ("|:--"*(len(row)-1))
        else:
            outstr += "**%s**|%s|**%s**\n" % (row[0], "|".join(row[1:-1]), row[-1])

    return outstr

def format_actions_discord(db, subreddit):
    def get_percentage(actions, total):
        try:
            return round((actions / total) * 100)
        except ZeroDivisionError:
            return 0

    outobj = {}
    daily_total = 0
    weekly_total = 0
    daily_cutoff = datetime.datetime.fromtimestamp(time.time() - (60 * 60 * 24))
    weekly_cutoff = datetime.datetime.fromtimestamp(time.time() - (60 * 60 * 24 * 7))
    mods = [str(m) for m in get_mods(subreddit, db)]

    daily_actions = db.get_total_mod_actions(mods, subreddit, since = daily_cutoff)
    daily_total = sum(daily_actions.values())
    weekly_actions = db.get_total_mod_actions(mods, subreddit, since = weekly_cutoff)
    weekly_total = sum(weekly_actions.values())

    longestusername = max([len(m) for m in mods])
    outstr = "For a detailed list, click above.\n```\n"
    outstr += "-"*(longestusername + 23) + "\n"
    for mod in mods:
        outstr += "%-{0}s %3s %2s%%  %4s %3s%% %3s\n".format(longestusername) % (
            mod, 
            daily_actions[mod], get_percentage(daily_actions[mod], daily_total), 
            weekly_actions[mod], get_percentage(weekly_actions[mod], weekly_total), 
            db.get_mods_last_action(subreddit, mod)
        )
    outstr += "-"*(longestusername + 23) + "\n"
    outstr += "%{0}s%4s      %5s\n".format(longestusername) % ("Total:", daily_total, weekly_total)
    outstr += "-"*(longestusername + 23) + "\n"
    outstr += "```\n(Bots aren't included)"
    
    return outstr
    
if __name__ == "__main__":
    with database.Database() as db:
        # for subreddit_name in db.get_subreddits():
        #     format_actions(db, subreddit_name, None, True)
        #     print("\n\n\n\n")

        # print(format_actions_reddit(db, "comedyheaven", datetime.datetime(2020, 8, 1), False))

        import discord
        discord.send_message(
            "https://discordapp.com/api/webhooks/585930332885483531/_ubxciybQnTHqv17XECg9LL5I6r-Lhq2JZvB3q9-3Ln2Qv_sGkAKHDewP9Ct81oO1nMD",
            "comedyheaven",
            "https://redd.it/abcdef",
            "https://i.imgur.com/2xnGazz.png",
            format_actions_discord(db, "comedyheaven")
        )
