import os
os.chdir("/root/SubredditModActionsLog")

import numpy as np
import imgurpython
import subreddit
import database
import datetime
import discord
import graph
import time

def format_actions_reddit(db, subreddit_name, since = None, vertical = False):
    """Gets and formats subreddit actions data from a given subreddit
    into a reddit formatted table.

    Args:
        db (database.Database): This application's database
        subreddit (str): A subreddit from which to get actions data
        since (datetime.datetime, optional): Only get data from past 
        this date. Use None to get all. Defaults to None.
        vertical (bool, optional): Makes the resulting table
        vertical instead of horizontal. Defaults to False.

    Returns:
        str: The reddit formatted table as a string
    """
    subreddit.logging.info("Started formatting for reddit: /r/%s @ %s..." % (subreddit_name, since))
    outobj = {}
    mods = subreddit.get_mods(subreddit_name, db)
    grand_total = 0

    #first of all we need to add zeros where there are no actions.
    #but we don't know the actions at this point, so this isn't
    #trivial. We use a dictionary:
    for c, mod in enumerate(mods, 0):   
        subreddit.logging.info("Getting actions from /u/%s (%i/%i)..." % (mod, c+1, len(mods)))    
        action_names_dealt_with = set()
        for action_name, times in db.get_actions(subreddit_name, mod, since):
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

    subreddit.logging.info("Calculating totals...")
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
        subreddit.logging.info("Flipped table...")

    subreddit.logging.info("Formatting as string...")
    outstr = ""
    for c, row in enumerate(outtable, 1):
        if c == 1 or c == len(outtable):
            outstr += "**%s**\n" % "**|**".join(row)
            if c == 1:
                outstr += ":--%s\n" % ("|:--"*(len(row)-1))
        else:
            outstr += "**%s**|%s|**%s**\n" % (row[0], "|".join(row[1:-1]), row[-1])

    subreddit.logging.info("Completed.")
    return outstr

def format_actions_discord(db, subreddit_name):
    """Gets total actions of each user and formats it so it can be sent in a discord
    webhook.

    Args:
        db (database.Database): This applications database.Database object
        subreddit (str): The name of the subreddit from which to get data
    """
    def get_percentage(actions, total):
        try:
            return round((actions / total) * 100)
        except ZeroDivisionError:
            return 0

    subreddit.logging.info("Started formatting for discord: /r/%s" % subreddit_name)
    outobj = {}
    daily_total = 0
    weekly_total = 0
    daily_cutoff = datetime.datetime.fromtimestamp(time.time() - (60 * 60 * 24))
    weekly_cutoff = datetime.datetime.fromtimestamp(time.time() - (60 * 60 * 24 * 7))
    mods = [str(m) for m in subreddit.get_mods(subreddit_name, db)]

    subreddit.logging.info("Getting today's actions...")
    daily_actions = db.get_total_mod_actions(mods, subreddit_name, since = daily_cutoff)
    daily_total = sum(daily_actions.values())
    subreddit.logging.info("Getting this week's actions...")
    weekly_actions = db.get_total_mod_actions(mods, subreddit_name, since = weekly_cutoff)
    weekly_total = sum(weekly_actions.values())

    subreddit.logging.info("Formatting as string and getting latest actions...")
    longestusername = max([len(m) for m in mods])
    outstr = "For a detailed list, click above.\n```\n"
    outstr += "-"*(longestusername + 24) + "\n"
    for mod in mods:
        outstr += "%-{0}s %3s %2s%%  %4s %3s%% %4s\n".format(longestusername) % (
            mod, 
            daily_actions[mod], get_percentage(daily_actions[mod], daily_total), 
            weekly_actions[mod], get_percentage(weekly_actions[mod], weekly_total), 
            db.get_mods_last_action(subreddit_name, mod)
        )
    outstr += "-"*(longestusername + 24) + "\n"
    outstr += "%{0}s%4s     %5s\n".format(longestusername) % ("Total:", daily_total, weekly_total)
    outstr += "-"*(longestusername + 24) + "\n"
    outstr += "```\n(Bots aren't included)"
    
    subreddit.logging.info("Completed.")
    return outstr

def draw_graph(db, subreddit_name, a_month_ago, a_week_ago):     
    subreddit.logging.info("Started making graph...")
    actions_to_get = db.get_chart_colors(subreddit_name, "line")

    longterm_actions = db.get_graph_stats(
        subreddit_name, actions_to_get = actions_to_get, 
        since = a_month_ago
    )
    subreddit.logging.info("Got longterm actions...")
    shortterm_actions =  db.get_graph_stats(
        subreddit_name, 
        actions_to_get = actions_to_get, 
        since = a_week_ago
    )
    subreddit.logging.info("Got shortterm actions...")

    actions_to_get = db.get_chart_colors(subreddit_name, "bar")
    stats = db.get_bar_graph_stats(
        actions_to_get, subreddit.get_mods(subreddit_name, db), 
        subreddit_name, a_week_ago
    )
    subreddit.logging.info("Got bar chart actions...")

    path = graph.draw_graph(longterm_actions, shortterm_actions, stats)
    subreddit.logging.info("Drew graph... Completed.")
    return path

def post_graph(impath, subreddit_name):
    subreddit.logging.info("Uploading to imgur...")
    client = imgurpython.ImgurClient(**database.CONFIG["imgurapi"])
    info = "/r/%s statistics graph: %s" % (subreddit_name, str(datetime.datetime.now()))

    image = client.upload_from_path(impath, config={
        "album": None,
        "name": info,
        "title": info,
        "description": info
    })
    return image["link"]

def post_subreddit_stats(db, subreddit_name, testing = False):
    subreddit.logging.info("Started onceaday routine for /r/%s" % subreddit_name)
    a_day_ago = datetime.datetime.fromtimestamp(time.time() - 60*60*24)
    a_week_ago = datetime.datetime.fromtimestamp(time.time() - 60*60*24*8)
    a_month_ago = datetime.datetime.fromtimestamp(time.time() - 60*60*24*31)
    graph_url = post_graph(draw_graph(db, subreddit_name, a_month_ago, a_week_ago), subreddit_name)
    subreddit.logging.info("Uploaded graph to %s" % graph_url)

    reddit_text = "## /r/%s moderator actions\n\n### In the last 24h:\n\n" % subreddit_name
    reddit_text += format_actions_reddit(db, subreddit_name, since = a_day_ago, vertical=True)
    reddit_text += "\n\n### 7 day rollover actions:\n\n"
    reddit_text += format_actions_reddit(db, subreddit_name, since = a_week_ago, vertical=True)
    reddit_text += "\n\nAutomatically generated by /u/jwnskanzkwk. [Source code](https://github.com/jwansek/SubredditModActionsLog)"

    subreddit.logging.info("Started posting to reddit...")
    reddit_url = subreddit.post_stats(
        subreddit_name, db.get_posting_subreddit(subreddit_name), graph_url, reddit_text
    )
    subreddit.logging.info("Posted to reddit @ %s" % reddit_url)

    webhookurl = db.get_webhook(subreddit_name, testing = testing)
    if webhookurl is not None:
        discord.send_message(
            webhookurl,
            subreddit_name,
            reddit_url,
            graph_url,
            format_actions_discord(db, subreddit_name)
        )
        subreddit.logging.info("Posted to discord.")

def main():
    starttime = time.time()
    with database.Database() as db:
        for subreddit_name in db.get_subreddits():
            post_subreddit_stats(db, subreddit_name, testing = False)
    subreddit.logging.info("Operation completed. (%s)." % (str(datetime.timedelta(seconds = time.time() - starttime))))

if __name__ == "__main__":
    main()
