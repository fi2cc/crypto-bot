from google.cloud import secretmanager
import os

os.environ["GCP_PROJECT_ID"] = "decoded-shadow-461618-h4"


def get_secret(secret_name, version="latest"):
    project_id = os.environ["GCP_PROJECT_ID"]
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

telegram_bot_key = get_secret("TELEGRAM_BOT_KEY")
telegram_chat_id = get_secret("TELEGRAM_CHAT_ID")

print("Telegram Bot Key:", telegram_bot_key)
print("Telegram Chat ID:", telegram_chat_id)
