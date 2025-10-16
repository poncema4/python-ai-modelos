import os
from pathlib import Path

import azure.identity
import openai
import prompty
import rich
from dotenv import load_dotenv

# Setup the OpenAI client to use either Azure or GitHub Models
load_dotenv(override=True)
API_HOST = os.getenv("API_HOST", "github")
if API_HOST == "azure":
    credential = azure.identity.DefaultAzureCredential()
    token_provider = azure.identity.get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    client = openai.OpenAI(
        base_url=os.environ["AZURE_AI_ENDPOINT"] + "openai/v1/",
        api_key=token_provider,
    )
    MODEL_NAME = os.environ["AZURE_AI_CHAT_DEPLOYMENT"]
elif API_HOST == "github":
    client = openai.OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=os.environ["GITHUB_TOKEN"],
    )
    MODEL_NAME = os.getenv("GITHUB_MODEL", "openai/gpt-4o")

query = (
    "¡He estado en espera por 30 minutos solo para preguntar por mi equipaje! Esto es ridículo. ¿Dónde está mi maleta?"
)
response = "Lamento mucho la larga espera, debe haber sido frustrante. Entiendo que estés preocupado por tu equipaje. Déjame ayudarte a localizarlo de inmediato. ¿Podrías proporcionarme el número de etiqueta de tu maleta o los detalles de tu vuelo para poder rastrearlo?"


class FriendlinessEvaluator:
    def __init__(self, client):
        current_dir = Path(__file__).parent
        prompty_path = current_dir / "friendliness.prompty"
        self.prompt = prompty.load(prompty_path)
        self.client = client

    def __call__(self, *, response: str, **kwargs):
        messages = prompty.prepare(self.prompt, {"response": response})
        completion = self.client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            messages=messages,
        )
        return completion.choices[0].message.content


friendliness_eval = FriendlinessEvaluator(client)
friendliness_score = friendliness_eval(query=query, response=response)
rich.print(f"Friendliness score: {friendliness_score}")
