import subreddit
import database
import sys

if __name__ == "__main__":
    try:
        days = int(sys.argv[1])
    except:
        print("ERROR: You need to specify the number of days to archive")
    else:
        with database.Database() as db:
            subreddit.archive(db, days)
