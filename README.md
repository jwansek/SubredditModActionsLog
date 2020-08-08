# Subreddit Moderator Actions Logger

You're looking at the development branch. I'm in the process of switching the program
from working with SQLite3 and a local file to a MySQL database, as well as making many
other optimisation changes that enable it to monitor many subreddits at the same time.
Eventually this will be designed to work in a docker container.

Logs moderator actions into a database. Also posts moderator statistics to a discord webhook
and detailed statistics to a subreddit, with graphs, which look like this:

Graph example | Discord example
--------------|----------------
![Graph example](https://i.imgur.com/VTR2Fam.png)|![Discord example](https://i.imgur.com/8LCdW98.png)

## Your `config.json` should be something like the following:

```
{
    "redditapi":
    {
        "client_id": "xxxxxxxxxxxxxx",
        "client_secret": "xxxxxxxxxxxxxxxxxxxxxx",
        "username": "xxxxxxxxxxx",
        "password": "xxxxxxxxxxxxxxxxxx",
        "user_agent": "xxxxxxxxxxxxxxxxxxx"
    },
    "imgurapi":
    {
        "client_id": "xxxxxxxxxxxxxx",
        "client_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "mysql":
    {
        "host": "192.168.0.62",
        "port": 3306,
        "user": "root",
        "passwd": "xxxxxxxxxxxxxx",
        "database": "SubredditModLog"
    }
}
```

All other settings are in the database (WIP)
