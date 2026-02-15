from google import genai

api_key = 'AIzaSyCwTx6-aQnXJ9DFLOm6n2KmKHT7wH6d6NM'
client = genai.Client(api_key=api_key)

print("Available models:")
for model in client.models.list():
    print(f"  - {model.name}")
