import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv  # Import dotenv package
import random
from Pet import Pet

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "PetQuest.db") ##Default here if not set

#STATS_MAX_IVS? PET MAX ATTRIBUYTES
MAX_LEVEL = 10
ELEMENTAL_TYPE = 0 # 0 - Fire, 1 - water, 2- grass


class Database:
    def __init__(self):
        """Initialize the database connection"""
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
 
    def check_user_by_id(self, user_id):
        self.cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
        if self.cursor.fetchone():
            return True
        else:
            return False
    
    #USER TABLE
    ##ADD USER, returns false if user already exisits, returns true if the user is created
    def add_user(self, user_id):
        if (self.check_user_by_id(user_id)):
            return False
        else:
            self.cursor.execute("INSERT INTO user (user_id) VALUES (?)", (user_id,))
            return True
        
    def get_user(self, user_id):
        if (self.check_user_by_id(user_id)):
            self.cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
            self.conn.commit() #Commit the transaction
            return self.cursor.fetchone()
        else:
            print("User Not Found")
            return None
    
    #PET DATABASE
    #RETURNS A LIST OF ALL PETS THAT ARE ALIVE
    def get_alive_pets_by_user(self, user_id):

        if (self.check_user_by_id(user_id)):
            self.cursor.execute("SELECT * FROM pet WHERE user_id = ? AND is_alive = 1", (user_id,))
            return self.cursor.fetchall()
        else:
            print("User Not Found")
            return []
    
    def get_pet(self, user_id):
        """Retrieve all pets for a given user and return as Pet objects"""
        self.cursor.execute("""
            SELECT pet_id, user_id, name, type_id, birthday, is_alive, hunger, 
                HP_IV, ATK_IV, DEF_IV, SPEED_IV, LEVEL, LIFESPAN, XP, 
                ELEMENTAL_TYPE_ID, HP, ATK, DEF, SPEED, DECAY_RATE
            FROM pet WHERE user_id = ? AND is_alive = 1
        """, (user_id,))
        pets = self.cursor.fetchall()
        if not pets:
            return None
        return [Pet(*pet) for pet in pets]  # Convert each row into a Pet object
    
    
    def add_pet(self, user_id, name,type_id,is_alive):
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        hunger = random.randint(10, 20) #10-20
        ELEMENTAL_TYPE = random.randint(0, 3)  #0-3
        HP_IV = random.randint(0, 10) #0-10
        ATK_IV = random.randint(0, 10) #10-30
        DEF_IV = random.randint(0, 10) #10-30
        SPEED_IV = random.randint(0, 10)#10-30

        HP = random.randint(10, 30) #0-10
        ATK = random.randint(10, 30) #10-30
        DEF = random.randint(10, 30) #10-30
        SPEED = random.randint(10, 30) #10-30
        DECAY_RATE = random.uniform(0, 1.0) #0->1.00%
        LEVEL = 0 # MAX 10
        XP = 0
        LIFESPAN = 0

        self.cursor.execute("INSERT INTO pet (user_id,name,type_id,birthday,is_alive,hunger,HP_IV,ATK_IV,DEF_IV,SPEED_IV,LEVEL,LIFESPAN,XP,ELEMENTAL_TYPE_ID, HP,ATK,DEF,SPEED,DECAY_RATE) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                            (user_id, 
                             name, 
                             type_id, 
                             current_time, 
                             is_alive,
                             hunger,
                             HP_IV,
                             ATK_IV,
                             DEF_IV,
                             SPEED_IV,
                             LEVEL,
                             LIFESPAN,
                             XP,
                             ELEMENTAL_TYPE,
                             HP,
                             ATK,
                             DEF,
                             SPEED,
                             DECAY_RATE
                             ))
        self.conn.commit() #Commit the transaction

    
    
    
    
    
    
    
'''

    def add_user(self, user_id, username):
        """Insert a new user if they don't exist"""
        signup_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("INSERT INTO users (user_id, username, signup_date) VALUES (?, ?, ?)", 
                            (user_id, username, signup_date))
        self.conn.commit()

    def user_exists(self, user_id):
        """Check if a user exists"""
        self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def hatch_pet(self, user_id, pet_name):
        """Hatch a pet for a user"""
        hatched_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("INSERT INTO pets (owner_id, pet_name, hatched_date) VALUES (?, ?, ?)", 
                            (user_id, pet_name, hatched_date))
        self.conn.commit()

    def has_pet(self, user_id):
        """Check if a user already has a pet"""
        self.cursor.execute("SELECT 1 FROM pets WHERE owner_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def close(self):
        """Close the database connection"""
        self.conn.close()
'''