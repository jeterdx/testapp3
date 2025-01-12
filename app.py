import os
from flask import Flask, redirect, render_template, request, send_from_directory, url_for
import pymongo
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Constants
MONGODB_DATABASE_NAME = "mitamura-paas-test-database"
MONGODB_COLLECTION_NAME = "collection1"
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-35-turbo"

# MongoDB setup
mongodb_client = pymongo.MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
mongodb_database = mongodb_client[MONGODB_DATABASE_NAME]
mongodb_collection = mongodb_database[MONGODB_COLLECTION_NAME]

# Azure OpenAI setup
azure_openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

app = Flask(__name__)

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/hello', methods=['POST'])
def hello():
    user_name = request.form.get('name')

    if not user_name:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))

    print(f'Request for hello page received with name={user_name}')

    generated_description = get_generated_description(user_name)
    insert_user_and_response_to_db(user_name, generated_description)

    return render_template('hello.html', name=user_name, ai_response=generated_description)

def get_generated_description(user_name):
    try:
        response = azure_openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Write a 10 words explanation about {user_name}."},
            ]
        )
        generated_description = response.choices[0].message.content
        print(generated_description)
        return generated_description
    except Exception as e:
        print(f"An error occurred while requesting api to Azure OpenAI: {e}")
        return "An error occurred while generating the description."

def insert_user_and_response_to_db(user_name, generated_description):
    user_document = {
        user_name: generated_description
    }
    try:
        result = mongodb_collection.insert_one(user_document)
        print(f"Document inserted with id: {result.inserted_id}")
    except Exception as e:
        print(f"An error occurred while inserting document: {e}")

if __name__ == '__main__':
    app.run()
