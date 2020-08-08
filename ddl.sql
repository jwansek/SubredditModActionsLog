CREATE DATABASE SubredditModLog;
USE SubredditModLog;

CREATE TABLE IF NOT EXISTS `subreddits` (
    `subreddit_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `subreddit` VARCHAR(40) NOT NULL,
    `post` VARCHAR(40) NOT NULL,
    `discord_webhook` CHAR(123) NULL,  
    `testing_webhook` CHAR(123) NULL
);

CREATE TABLE IF NOT EXISTS `bots` (
    `blacklist_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_name` VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS `subreddit_bots` (
    `subreddit_id` INT UNSIGNED NOT NULL REFERENCES `subreddits` (`subreddit_id`),
    `blacklist_id` INT UNSIGNED NOT NULL REFERENCES `bots` (`blacklist_id`),
    PRIMARY KEY (`subreddit_id`, `blacklist_id`)
);

CREATE TABLE IF NOT EXISTS `log` (
    `log_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `mod` VARCHAR(40) NOT NULL,
    `subreddit_id` INT UNSIGNED NOT NULL REFERENCES `subreddits` (`subreddit_id`),
    `action` VARCHAR(46) NOT NULL,
    `date` DATETIME NOT NULL,
    `permalink` VARCHAR(200) NULL,
    `notes` VARCHAR(400) NULL,
    `reddit_id` VARCHAR(50) NULL
);

INSERT INTO `subreddits` (`subreddit`, `post`, `discord_webhook`, `testing_webhook`) VALUES ("comedyheaven", "u_jwnskanzkwk", "https://discordapp.com/api/webhooks/xxxxxxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "https://discordapp.com/api/webhooks/xxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx");

INSERT INTO `bots` (`user_name`) VALUES ("AutoModerator");
INSERT INTO `bots` (`user_name`) VALUES ("RepostSentinel");
INSERT INTO `bots` (`user_name`) VALUES ("MAGIC_EYE_BOT");
INSERT INTO `bots` (`user_name`) VALUES ("BotBust");
INSERT INTO `bots` (`user_name`) VALUES ("BotDefense");
INSERT INTO `bots` (`user_name`) VALUES ("reddit");

INSERT INTO `subreddit_bots` VALUES (1, 1);
INSERT INTO `subreddit_bots` VALUES (1, 2);
INSERT INTO `subreddit_bots` VALUES (1, 3);

