import subreddit
import database

if __name__ == "__main__":
    with database.Database() as db:
        subreddit.archive(db, 1)