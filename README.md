# Subreddit Moderator Actions Logger

Logs moderator actions into a database. Also posts moderator statistics to a discord webhook
and detailed statistics to a subreddit, with graphs, which look like this:

Graph example | Discord example
--------------|----------------
![Graph example](https://i.imgur.com/VTR2Fam.png)|![Discord example](https://i.imgur.com/8LCdW98.png)

There are two programs involved:

* `modLogStream.py` which streams moderator actions and puts them in the database

* `onceaday.py` which is executed once every 24h and calculates statistics and the 
graph, then posts them to reddit and discord

* `oldLogProg.py` is an older version of the program which didn't stream actions,
but worked them all out at once. This was horribly ineffieient, requiring disk I/O
for week old actions and sometimes taking ovre 40 minutes to run. It's kept in case
the stream shuts down for some reason.

## TODO

* [ ] Merge the code from `webhooks.py` and `login.py` into the main program,
since it is not nessicary to have them in separate files any more

* [ ] Delete references to the old program

* [x] Move the database name, subreddit to log, and subreddit to post to to `credentials.json`
to make it possible to easily run the program with other subreddits 

* [x] Automatically create the table when it doesn't exist

* [ ] Make graph look better

## Your `credentials.json` should be something like the following:

```
{
    "subredditstream": "subredditforlogging",
    "subredditpost": "subredditforstats",
    "database": "YourDatabasePath.db",
    "bots":
    [
        "AutoModerator",
        "RepostSentinel",
        "MAGIC_EYE_BOT"
    ],
    "redditapi":
    {
        "client_id": "xxxxxxxxxxxxxx",
        "client_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "username": "xxxxxxxxxxxx",
        "password": "xxxxxxxxxxxxxxxxxxxxx",
        "user_agent": "xxxxxxxxxxxxxx"
    },
    "discordwebhooks":
    {
        "prodwebhook": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "testwebhook": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "imgurapi":
    {
        "client_id": "xxxxxxxxxxxxxxx",
        "client_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
}
```
