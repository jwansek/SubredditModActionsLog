import functools
import datetime
import pymysql
import sqlite3
import random
import json

with open("config.json", "r") as f:
    CONFIG = json.load(f)

class Database:
    def __enter__(self):
        self.__connection = pymysql.connect(
            **CONFIG["mysql"],
            charset = "utf8mb4",
            # cursorclass = pymysql.cursors.DictCursor
        )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def migrate_sqlite(self, sqlitefile, subreddit):
        conn = sqlite3.connect(sqlitefile)
        cur = conn.cursor()
        cur.execute("SELECT * FROM log;")
        log = cur.fetchall()
        cur.close()
        conn.close()

        #still can't get executemany to work :/
        with self.__connection.cursor() as cursor:
            for c, i in enumerate(log, 0):
                cursor.execute("""
                INSERT INTO log (`mod`, `subreddit_id`, `action`, `date`, `permalink`, `notes`, `reddit_id`)
                VALUES (%s, (
                    SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
                ), %s, %s, %s, %s, %s);
                """, (
                    i[1], subreddit, i[2], datetime.datetime.fromtimestamp(i[3]), i[4], i[5], i[6]
                ))
                print("Added log item from: %s %.2f%% complete" % (
                    datetime.datetime.fromtimestamp(i[3]).strftime("%b %d %Y %H:%M:%S"),
                    (c / len(log)) * 100
                ))

        self.__connection.commit()

    def get_tables(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            return cursor.fetchall()

    def reddit_id_in_db(self, reddit_id):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT reddit_id FROM log WHERE reddit_id = %s;", (reddit_id, ))
            return [i[0] for i in cursor.fetchall()] != []

    def get_ids(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT reddit_id FROM log;")
            return [i[0] for i in cursor.fetchall()]

    def database_call(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except pymysql.err.OperationalError as e:
                print("WARNING", e)
                func(self, *args, **kwargs)
        return wrapper

    @database_call
    def add_action(self, subreddit, reddit_id, mod, action, timestamp, permalink, notes, notes2):
        if self.reddit_id_in_db(reddit_id):
            print(" Skipped action from /r/%s by /u/%s at %s" % (
                subreddit, mod,
                datetime.datetime.fromtimestamp(timestamp).strftime("%b %d %Y %H:%M:%S")
            ))
            return

        if notes is None:
            notes = ""
        if notes2 is None:
            notes2 = ""
        notes = notes + " " + notes2

        with self.__connection.cursor() as cursor:           
            cursor.execute("""
            INSERT INTO log (`mod`, `subreddit_id`, `action`, `date`, `permalink`, `notes`, `reddit_id`)
            VALUES (%s, (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            ), %s, %s, %s, %s, %s);
            """, (
                mod, subreddit, action, datetime.datetime.fromtimestamp(timestamp), 
                permalink, notes, reddit_id
            ))
        
        print("/u/%-19s /r/%-15s %-15s %s %s" % (
            mod, subreddit, action, 
            datetime.datetime.fromtimestamp(timestamp).strftime("%b %d %Y %H:%M:%S"), notes
        ))      
        self.__connection.commit()

    def get_graph_stats(self, subreddit, mod = None, actions_to_get = [("all_actions", "blue")], since = None):
        """Function for returning data from the database which will be used
        to make a matplotlib graph.

        Args:
            subreddit (str): A subreddit from which to extract mod data from.
            actions_to_get (list, optional): A list of tuples of
            actions to get. The tuple consists of a reddit mod action and
            a colour that matplotlib understands. Use 'all_actions' to get all
            actions. Defaults to [("all_actions", "blue")].
            since (datetime.datetime, optional): Only get mod actions after
            this date. Defaults to datetime.datetime(1970, 1, 1).
        """
        if since is None:
            since = datetime.datetime(1970, 1, 1)

        def get_action_stats(cursor, action = "all_actions"): 
            sql = """
            SELECT DATE(`date`), COUNT(*) AS count FROM log 
            WHERE `subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            ) 
            AND `mod` NOT IN (
                SELECT `bots`.`user_name` FROM `bots` 
                INNER JOIN `subreddit_bots` ON `subreddit_bots`.`blacklist_id` = `bots`.`blacklist_id` 
                WHERE `subreddit_bots`.`subreddit_id` = (
                    SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
                )
            )
            AND `date` >= %s
            AND `action` IN (%s)
            AND `mod` = %s
            GROUP BY DATE(`date`);
            """
            args = (subreddit, subreddit, since, action[0])
            if action[0] == "all_actions":
                sql = sql.replace("AND `action` IN (%s)", "")
                args = args[:-1]

            if mod is None:
                sql = sql.replace("AND `mod` = %s", "")
            else:
                args = args + (mod, )
            
            cursor.execute(sql, args)
            return cursor.fetchall()

        with self.__connection.cursor() as cursor:
            return {a: self.reorder_lists(get_action_stats(cursor, a)) for a in actions_to_get}

    def get_bar_graph_stats(self, actions_to_get, mods, subreddit, since = None):
        assert len(actions_to_get) >= 1
        assert len(actions_to_get[0]) == 2
        if since is None:
            since = datetime.datetime(1970, 1, 1)
        mods = [str(mod) for mod in mods]
        actions = [i[0] for i in actions_to_get]

        def get_misc(cursor):
            cursor.execute("""
            SELECT `mod`, COUNT(`mod`)
            FROM `log`
            WHERE `subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            )
            AND `mod` IN %s
            AND `action` NOT IN %s
            AND `date` >= %s
            GROUP BY `mod`
            """, (subreddit, mods, actions, since))
            out = list(cursor.fetchall())
            #add zeroes
            for mod in mods:
                if mod not in [i[0] for i in out]:
                    out.append((mod, 0))
            return [i[1] for i in sorted(out, key = lambda i: mods.index(i[0]))]

        def get_mods_actions(cursor, mod):
            sql = """
            SELECT `action`, COUNT(`action`)
            FROM `log` WHERE `subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            )
            AND `mod` = %s
            AND `action` IN %s
            AND `date` >= %s
            GROUP BY `action`;
            """
            # print(sql % (subreddit, mod, actions, since))
            cursor.execute(sql, (subreddit, mod, actions, since))
            out = [list(i) for i in cursor.fetchall()]

            #add zeroes where there are no actions
            for action in actions:
                if out == []:
                    out.append([action, 0])
                else:
                    if action not in [i[0] for i in out]:
                        out.append([action, 0])
         
            return out

        def to_matplotlib_format(orig, actions):
            out = {action: [] for action in actions}
            for i in orig:
                for j in i:
                    out[j[0]].append(j[1])
            return out

        with self.__connection.cursor() as cursor:
            out = to_matplotlib_format([get_mods_actions(cursor, mod) for mod in mods], actions)
            out["misc"] = get_misc(cursor)
            actions_to_get.append(("misc", "grey"))
            return [mods, out, {i[0]: i[1] for i in actions_to_get}]

    def get_chart_colors(self, subreddit, chart):
        assert chart in ["bar", "line"]
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT `chart_action_colours`.`action`, `chart_action_colours`.`color` 
            FROM `chart_action_colours` 
            INNER JOIN `chart_colours` 
            ON `chart_colours`.`bar_colours` = `chart_action_colours`.`chart_color_id` 
            WHERE `chart_colours`.`subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            )
            AND `chart_colours`.`chart_type` = %s
            ; 
            """, (subreddit, chart))
            return list(cursor.fetchall())

    def reorder_lists(self, list_):
        """Converts a list of lists into two lists that matplotlib likes"""
        return [[i[0] for i in list_], [i[1] for i in list_]]

    def get_mods_last_action(self, subreddit, mod):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT IFNULL(
                CONCAT(FLOOR((UNIX_TIMESTAMP(NOW()) - UNIX_TIMESTAMP(MAX(`date`))) / 60 / 60 / 24), "d"), 
                "∞"
            ) 
            FROM `log` WHERE `mod` = %s AND `subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            );
            """, (mod, subreddit))
            return cursor.fetchone()[0]

    def get_actions(self, subreddit, mod = None, since = None):
        if since is None:
            since = datetime.datetime(1970, 1, 1)

        sql = """
        SELECT `action`, COUNT(`action`) FROM `log` 
        WHERE `subreddit_id` = (
            SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
        )
        AND `date` >= %s
        AND `mod` = %s
        GROUP BY `action`;
        """
        args = (subreddit, since, str(mod))
        if mod is None:
            sql = sql.replace("AND `mod` = %s", """
        AND `mod` NOT IN (
            SELECT `bots`.`user_name` FROM `bots` 
            INNER JOIN `subreddit_bots` 
            ON `subreddit_bots`.`blacklist_id` = `bots`.`blacklist_id` 
            WHERE `subreddit_bots`.`subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            )
        )
            """)
            args = (subreddit, since, subreddit) 

        with self.__connection.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()

    def get_bots(self, subreddit):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT `bots`.`user_name` FROM `bots` 
            INNER JOIN `subreddit_bots` 
            ON `subreddit_bots`.`blacklist_id` = `bots`.`blacklist_id` 
            WHERE `subreddit_bots`.`subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            );
            """, (subreddit, ))
            return [i[0] for i in cursor.fetchall()]

    def get_subreddits(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT `subreddit` FROM `subreddits`;")
            return [i[0] for i in cursor.fetchall()]

    def get_webhook(self, subreddit, testing = False):
        with self.__connection.cursor() as cursor:
            if testing:
                cursor.execute("""
                SELECT `testing_webhook` FROM `subreddits` WHERE `subreddit` = %s
                """, (subreddit, ))
            else:
                cursor.execute("""
                SELECT `discord_webhook` FROM `subreddits` WHERE `subreddit` = %s
                """, (subreddit, ))
            return cursor.fetchone()[0]

    def get_posting_subreddit(self, subreddit):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT `post` FROM `subreddits` WHERE `subreddit` = %s
            """, (subreddit, ))
            return cursor.fetchone()[0]

    def get_total_mod_actions(self, moderators, subreddit, since = None):
        if since is None:
            since = datetime.datetime(1970, 1, 1)
        moderators = [str(m) for m in moderators]

        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT `mod`, COUNT(`mod`), 0 FROM `log`
            WHERE `date` >= %s
            AND `mod` IN %s
            AND `subreddit_id` = (
                SELECT `subreddit_id` FROM `subreddits` WHERE `subreddit` = %s
            )
            GROUP BY `mod`;
            """, (since, moderators, subreddit))
            outobj = {i[0]: i[1] for i in cursor.fetchall()}
        
        for mod in moderators:
            if mod not in outobj.keys():
                outobj[mod] = 0

        return outobj

if __name__ == "__main__":
    with Database() as db:
        # db.migrate_sqlite("ComedyHeavenModLog.db", "comedyheaven")
        
        #import subreddit
        #import time
        #print(db.get_bar_graph_stats(
        #    db.get_chart_colors("SmallYTChannel", "bar"), 
        #    subreddit.get_mods("SmallYTChannel", db),
        #    "SmallYTChannel",
        #    datetime.datetime.fromtimestamp(time.time() - 60*60*24*8)
        #))
        import time

        db.add_action("SmallYTChannel", "abcdef", "jwnskanzkwk", "test", int(time.time()), "redd.it/abcdef", "", "")
