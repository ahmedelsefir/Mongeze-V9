# firebase_setup.py

"""
This script sets up Firebase users with admin and client roles.
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth

# Initialize Firebase Admin SDK
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Function to add a new user

def add_user(email, password, role):
    user = auth.create_user(
        email=email,
        password=password
    )
    # Assign the role to the user
    if role in ['admin', 'client']:
        auth.set_custom_user_claims(user.uid, {"role": role})
    print(f'User {email} added with role {role}')

# Function to update existing user roles

def update_user_role(uid, role):
    if role in ['admin', 'client']:
        auth.set_custom_user_claims(uid, {"role": role})
        print(f'User {uid} role updated to {role}')

# Function to display current users

def display_users():
    users = auth.list_users().users
    for user in users:
        print(f'User {user.email} 

# Example usage:
# add_user('user@example.com', 'password123', 'client')
# update_user_role('uid_of_user', 'admin')
# display_users()
