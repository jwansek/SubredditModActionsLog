from discord_webhooks import DiscordWebhooks

def send_message(webhookurl, subreddit, link, image, text):
    """Send a webhook message to a given discord server channel.

    Args:
        webhookurl (str): A discord webhook URL
        subreddit (str): The subreddit concerning the title
        link (str): Link to the main reddit post with more data
        image (str): Link to the imgur graph image
        text (str): Formatted text table to be shown in the webhook
    """
    webhook = DiscordWebhooks(webhookurl)
    webhook.set_content(title = "/r/%s Moderator Actions" % subreddit)
    webhook.set_image(url = image)
    webhook.send()
    #sending two webhooks is the only way that the text is formatted nicely
    #on both mobile and desktop with the image
    #this is because discord's CSS is really shitty.

    webhook = DiscordWebhooks(webhookurl)
    webhook.set_content(
        content = link,
        description = text
    )
    webhook.set_footer(
        text='@eden#7623\nhttps://github.com/jwansek/SubredditModActionsLog', 
        icon_url='https://avatars1.githubusercontent.com/u/37976823?s=460&u=1739eabb8af515eccf259a9eb5ad7f44ac6aed85&v=4'
    )
    webhook.send()
