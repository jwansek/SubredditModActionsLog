from discord_webhooks import DiscordWebhooks
import login

if login.PRODUCTION:
    WEBHOOK_URL = login.DISCORD.prodwebhook
else:
    WEBHOOK_URL = login.DISCORD.testwebhook

def send_message(url, text, impath):
    webhook = DiscordWebhooks(WEBHOOK_URL)
    webhook.set_content(title = "/r/%s Moderator Actions" % login.data["subredditstream"], content = url, description = text)
    webhook.set_image(url = impath)
    webhook.send()
