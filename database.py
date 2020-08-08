import datetime
import pymysql
import sqlite3
import graph
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
        
        print("/u/%-19s /r/%s %-15s %s %s" % (
            mod, subreddit, action, 
            datetime.datetime.fromtimestamp(timestamp).strftime("%b %d %Y %H:%M:%S"), notes
        ))      
        self.__connection.commit()

    def get_graph_stats(self, subreddit, actions_to_get = [("all_actions", "blue")], since = None):
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
            GROUP BY DATE(`date`);
            """
            args = (subreddit, subreddit, since, action[0])
            if action[0] == "all_actions":
                sql = sql.replace("AND `action` IN (%s)", "")
                args = args[:-1]
            
            cursor.execute(sql, args)
            return cursor.fetchall()

        with self.__connection.cursor() as cursor:
            return {a: self.reorder_lists(get_action_stats(cursor, a)) for a in actions_to_get}

    def reorder_lists(self, list_):
        """Converts a list of lists into two lists that matplotlib likes"""
        return [[i[0] for i in list_], [i[1] for i in list_]]

    def get_mods_last_action(self, subreddit, mod):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT IFNULL(
                FLOOR((UNIX_TIMESTAMP(NOW()) - UNIX_TIMESTAMP(MAX(`date`))) / 60 / 60 / 24), 
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
        # db.migrate_sqlite("SYTCModLog.db", "SmallYTChannel")
        # graph.draw_graph(db.get_graph_stats("comedyheaven", [("removelink", "red"), ("approvelink", "green")]))
        print(db.get_mods_last_action("comedyheaven", "chompythebeast"))
        # for i in db.get_actions("SmallYTChannel", "jwnskanzkwk"):
        #     print(i)

        # print(db.get_total_mod_actions(["jwnskanzkwk", "doctopi"]))
