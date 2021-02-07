# Subreddit Moderator Actions Logger

Logs moderator actions into a database. Also posts moderator statistics to a discord webhook
and detailed statistics to a subreddit, with graphs, which look like this:

Graph example | Discord example
--------------|----------------
![Graph example](https://i.imgur.com/Xx39NqZ.png)|![Discord example](https://i.imgur.com/7gKBCEm.png)
![Graph example 2](https://i.imgur.com/ZLgydsF.png)|![Discord example 2](https://i.imgur.com/kwV7wcL.png)

## Docker

The program is designed to be run in a docker container.

 - Set up a MySQL database and build tables, like `ddl.sql`
 - `sudo docker build -t jwansek/subredditmodlog .`
 - `sudo docker run -d --name subredditmodlog --net=host jwansek/subredditmodlog`

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

All other settings are in the database (see `ddl.sql`)
