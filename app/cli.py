import typer
from typing import Annotated
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    '''
    Creates an empty database and adds a default user ''bob'
    '''
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        # bob = User(username="bob", email="bob@mail.com", password="bobpass") # Create a new user (in memory)
        bob = User("bob", "bob@mail.com", "bobpass") # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username: Annotated[str, typer.Argument(help="The name of the user to be searched for")]):
    '''
    Prints user information given the username
    '''
    with get_session() as db: 
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    '''
    Prints all users that exist within the database
    '''
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(
    username: Annotated[str, typer.Argument(help="Username of record to change the email of")], 
    new_email: Annotated[str, typer.Argument(help="New email to replace existing email address")]
):
    '''
    Changes the email of the provided username record to the given new email address
    '''
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: Annotated[str, typer.Argument(help="Username of new record")], 
    email: Annotated[str, typer.Argument(help="Email address of new record")], 
    password: Annotated[str, typer.Argument(help="Password of new record")]
):
    '''
    Create a new user given username, email and password and adds it to the database
    '''
    with get_session() as db:
        # newuser = User(username=username, email=email, password=password)
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(newuser)

@cli.command()
def delete_user(username: Annotated[str, typer.Argument(help="Username of the record to remove from the database")]):
    '''
    Deletes a single user from the database given a username
    '''
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

@cli.command()
def find_by_email(email: Annotated[str, typer.Argument(help="Email address to search by")]):
    '''
    Searches database for partial matches to the provided email and prints all possible matching records
    '''
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                if email in user.email:
                    print(user)

@cli.command()
def list_num_users(
    limit: Annotated[int, typer.Argument(help="Specifies the number of users to print")] = 10, 
    offset: Annotated[int, typer.Argument(help="Specifies where the listing should start from ")] = 0
):
    '''
    Prints the number specified in limit amount of records starting at the offset value in the database
    '''
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for i in range(offset, min(offset + limit, len(all_users))):
                print(all_users[i])

if __name__ == "__main__":
    cli()
