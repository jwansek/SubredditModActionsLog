CREATE DATABASE SubredditModLog;
USE SubredditModLog;

CREATE TABLE IF NOT EXISTS `subreddits` (
    `subreddit_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `subreddit` VARCHAR(40) NOT NULL,
    `post` VARCHAR(40) NOT NULL,
    `discord_webhook` CHAR(123) NULL,  
    `testing_webhook` CHAR(123) NULL
);
INSERT INTO `subreddits` (`subreddit`, `post`, `discord_webhook`, `testing_webhook`) VALUES ("comedyheaven", "u_jwnskanzkwk", "https://discordapp.com/api/webhooks/xxxxxxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "https://discordapp.com/api/webhooks/xxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx");

CREATE TABLE IF NOT EXISTS `bots` (
    `blacklist_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_name` VARCHAR(40) NOT NULL
);
INSERT INTO `bots` (`user_name`) VALUES ("AutoModerator");
INSERT INTO `bots` (`user_name`) VALUES ("RepostSentinel");
INSERT INTO `bots` (`user_name`) VALUES ("MAGIC_EYE_BOT");
INSERT INTO `bots` (`user_name`) VALUES ("BotBust");
INSERT INTO `bots` (`user_name`) VALUES ("BotDefense");
INSERT INTO `bots` (`user_name`) VALUES ("reddit");

CREATE TABLE IF NOT EXISTS `subreddit_bots` (
    `subreddit_id` INT UNSIGNED NOT NULL REFERENCES `subreddits` (`subreddit_id`),
    `blacklist_id` INT UNSIGNED NOT NULL REFERENCES `bots` (`blacklist_id`),
    PRIMARY KEY (`subreddit_id`, `blacklist_id`)
);
INSERT INTO `subreddit_bots` VALUES (1, 1);
INSERT INTO `subreddit_bots` VALUES (1, 2);
INSERT INTO `subreddit_bots` VALUES (1, 3);

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

CREATE TABLE IF NOT EXISTS `chart_action_colours` (
    `chart_color_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `action` VARCHAR(46) NOT NULL,
    `color` VARCHAR(15) NOT NULL
);
INSERT INTO `chart_action_colours` (`action`, `color`) VALUES ("approvelink", "green");
INSERT INTO `chart_action_colours` (`action`, `color`) VALUES ("removelink", "red");
INSERT INTO `chart_action_colours` (`action`, `color`) VALUES ("removecomment", "orange");

CREATE TABLE IF NOT EXISTS `chart_colours` (
    `subreddit_id` INT UNSIGNED NOT NULL REFERENCES `subreddits` (`subreddit_id`),
    `bar_colours` INT UNSIGNED NOT NULL REFERENCES `chart_action_colours` (`chart_color_id`),
    `chart_type` CHAR(4) NOT NULL CHECK (`chart_type` IN ("bar", "line")),
    PRIMARY KEY (`subreddit_id`, `bar_colours`, `chart_type`)
);
INSERT INTO `chart_colours` VALUES (1, 1, "line");
INSERT INTO `chart_colours` VALUES (1, 3, "line");
INSERT INTO `chart_colours` VALUES (1, 1, "bar");
INSERT INTO `chart_colours` VALUES (1, 3, "bar");
INSERT INTO `chart_colours` VALUES (1, 2, "bar");

CREATE TABLE IF NOT EXISTS `error_log` (
    `error_id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `status` VARCHAR(15) NOT NULL,
    `text` VARCHAR(100) NOT NULL,
    `datetime` DATETIME NOT NULL DEFAULT NOW()
);