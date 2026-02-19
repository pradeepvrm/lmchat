import os
from dotenv import load_dotenv
from appwrite.id import ID
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.users import Users

load_dotenv()

client = Client()

client.set_endpoint(os.getenv('appwrite_endpoint'))
client.set_project(os.getenv('appwrite_project'))
client.set_key(os.getenv('appwrite_key'))

users = Users(client)

def get_session_client():
    client = Client()
    client.set_endpoint(os.getenv('appwrite_endpoint'))
    client.set_project(os.getenv('appwrite_project'))
    return client

def create(name, email, password):
    response = users.create(
        user_id= ID.unique(),
        name= name,
        email= email,
        password= password
    )
    return response

def create_session(email, password):
    account = Account(client)
    response = account.create_email_password_session(email, password)
    return response

def create_anonymous_session():
    account = Account(client)
    response = account.create_anonymous_session()
    return response

def register_from_session(session_secret, name, email, password):
    client = get_session_client()
    client.set_session(session_secret)
    account = Account(client)
    account.update_name(name)
    response = account.update_email(email, password)
    return response
