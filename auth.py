import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.account import Account

load_dotenv()

client = Client()

client.set_endpoint(os.getenv('appwrite_endpoint'))
client.set_project(os.getenv('appwrite_project'))
client.set_key(os.getenv('appwrite_key'))

account = Account(client)

def create_session(email, password):
    response = account.create_email_password_session(email, password)
    return response

def get_user():
    user = account.get()
    return user

def logout():
    try:
        account.delete_sessions()
        return True
    finally:
        print("error in logout!!")