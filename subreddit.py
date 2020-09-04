import database
import datetime
import logging
import praw
import time
import json
import os

REDDIT = praw.Reddit(**database.CONFIG["redditapi"])

logging.basicConfig( 
    format = "%(process)s\t[%(asctime)s]\t%(message)s", 
    level = logging.INFO,
    handlers=[
        logging.FileHandler("onceaday.log"),
        logging.StreamHandler()
    ])

def get_mods(subreddit, db):
    """Get the moderators from a given subreddit.

    Args:
        subreddit (str): The subreddit to get mods
        db (database.Database): This application's database.Database

    Returns:
        list: List of PRAW redditors who are mods
    """
    return [
        i for i in REDDIT.subreddit(subreddit).moderator() 
        if str(i) not in db.get_bots(subreddit)
    ]

def post_stats(subreddit_name, post_to, imurl, text):
    submission = REDDIT.subreddit(post_to).submit(
        "/r/%s Mod Actions: %s" % (subreddit_name, str(datetime.datetime.now())),
        url = imurl
    )
    if len(text) >= 10000:
        text = "Data too long to be shown; greater than 10000 characters"
        logging.error("{ERROR} too many characters for reddit comment")

    submission.reply(text).mod.distinguish(sticky = True)
    return "https://redd.it/%s" % submission.id

def stream(db):
    """Streams moderator actions from all subreddits and adds them
    to the database as they come in.

    Args:
        db (database.Database): A database object to add to
    """
    streams = [REDDIT.subreddit(s).mod.stream.log(pause_after=-1) for s in db.get_subreddits()]
    while True:
        for stream in streams:
            for action in stream:
                if action is None:
                    break

                db.add_action(
                    str(action.subreddit), str(action.id), str(action.mod), action.action, 
                    int(action.created_utc), action.target_permalink, action.details, action.description
                )

def archive(db, oldest_action):
    """Archives previous moderator actions to the database. Can be used
    when the stream function hasn't been working for a while.

    Args:
        db (database.Database): A database object to add to
        oldest_action (int): The oldest action in days to add before stopping
    """
    for subreddit in [REDDIT.subreddit(s) for s in db.get_subreddits()]:
        for mod in subreddit.moderator():
            mod = str(mod)

            for action in subreddit.mod.log(mod = mod, limit = None):
                daysago = (time.time() - action.created_utc) / 60 / 60 / 24
                if daysago > oldest_action:
                    break
                
                db.add_action(
                    str(action.subreddit), str(action.id), str(action.mod), action.action, 
                    int(action.created_utc), action.target_permalink, action.details, action.description
                )

def main():
    write_pid()
    with database.Database() as db:
        stream(db)

def write_pid():
    with open("sml.json", "w") as f:
        json.dump(os.getpid(), f)

if __name__ == "__main__":
    main()


