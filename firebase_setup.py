# firebase_setup.py

"""
This script sets up Firebase users with admin and client roles.
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Function to add a new user

def add_user(email, password, role):
    """
    Create a new Firebase user and assign a role.
    
    Args:
        email: User email address
        password: User password
        role: User role ('admin' or 'client')
    
    Returns:
        The created user record, or None on failure
    
    Raises:
        ValueError: If role is not 'admin' or 'client'
    """
    if role not in ['admin', 'client']:
        raise ValueError(f"Invalid role '{role}'. Must be 'admin' or 'client'.")
    
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
    except auth.EmailAlreadyExistsError:
        logger.error(f"User with email {email} already exists")
        raise
    except Exception as e:
        logger.error(f"Failed to create user {email}: {e}")
        raise

    try:
        auth.set_custom_user_claims(user.uid, {"role": role})
    except Exception as e:
        logger.error(f"User {email} created but failed to assign role '{role}': {e}")
        raise

    logger.info(f"User {email} added with role {role}")
    return user

# Function to update existing user roles

def update_user_role(uid, role):
    """
    Update the role for an existing Firebase user.
    
    Args:
        uid: Firebase user UID
        role: New role ('admin' or 'client')
    
    Raises:
        ValueError: If role is not 'admin' or 'client'
    """
    if role not in ['admin', 'client']:
        raise ValueError(f"Invalid role '{role}'. Must be 'admin' or 'client'.")
    
    try:
        auth.set_custom_user_claims(uid, {"role": role})
        logger.info(f"User {uid} role updated to {role}")
    except auth.UserNotFoundError:
        logger.error(f"User {uid} not found — cannot update role")
        raise
    except Exception as e:
        logger.error(f"Failed to update role for user {uid}: {e}")
        raise

# Function to display current users

def display_users():
    """List all Firebase users with their email and UID."""
    try:
        users = auth.list_users().users
        for user in users:
            print(f"User {user.email} (UID: {user.uid})")
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise

# Example usage:
# add_user('user@example.com', 'password123', 'client')
# update_user_role('uid_of_user', 'admin')
# display_users()
