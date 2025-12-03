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

account = Account(client)
users = Users(client)

def create(name, email, password):
    response = users.create(
        user_id= ID.unique(),
        name= name,
        email= email,
        password= password
    )
    return response

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