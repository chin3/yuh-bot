from enum import Enum
from datetime import datetime, timedelta

class ElementalType(Enum):
    WATER = 0 #Blue
    GRASS = 1 #Dark Green
    FIRE = 2  #RED
    ICE = 3   #Light Blue
    ELECTRIC = 4 #Yellow
    WIND = 5 #Silver
    ROCK = 6 #Brown
    NUCLEAR = 7 #Bright Green

class SpeciesType(Enum):
    DOG = 0
    CAT = 1
    RAT = 2
    CAPYBARA = 3
    HAMSTER = 4
    PANDA = 5
    MONKEY = 6
    BIRD = 7
    HEDGEHOG = 8
    BUNNY = 9
    SLOTH = 10



class Pet:
    MAX_HUNGER = 100  # Maximum hunger level
    BASE_LIFESPAN_INCREASE = 6  # Feeding increases lifespan by 6 hours
    HOURLY_HUNGER_INCREASE = 4  # Hunger increases by 2 per hour
    HOURLY_DECAY_MULTIPLIER = 0.5  # Decay rate applied per hour

    def __init__(self, pet_id, user_id, name, type_id, birthday, is_alive, hunger, 
                 HP_IV, ATK_IV, DEF_IV, SPEED_IV, LEVEL, LIFESPAN, XP, ELEMENTAL_TYPE_ID, 
                 HP, ATK, DEF, SPEED, DECAY_RATE):
        self.pet_id = pet_id
        self.user_id = user_id
        self.name = name
        self.type_id = type_id
        self.birthday = datetime.strptime(birthday, "%Y-%m-%d %H:%M:%S")
        self.is_alive = bool(is_alive)
        self.hunger = hunger
        self.HP_IV = HP_IV
        self.ATK_IV = ATK_IV
        self.DEF_IV = DEF_IV
        self.SPEED_IV = SPEED_IV
        self.LEVEL = LEVEL
        self.LIFESPAN = LIFESPAN  # Now in hours instead of days
        self.XP = XP
        self.ELEMENTAL_TYPE_ID = ELEMENTAL_TYPE_ID
        self.HP = HP
        self.ATK = ATK
        self.DEF = DEF
        self.SPEED = SPEED
        self.DECAY_RATE = DECAY_RATE
        self.MaxHP = self.HP_IV + self.HP
        self.MaxATK = self.ATK_IV + self.ATK
        self.MaxDEF = self.DEF_IV + self.DEF
        self.MaxSPEED = self.SPEED_IV + self.SPEED
        self.last_fed = datetime.utcnow()

    def feed(self, food_value=20):
        """Feed the pet to reduce hunger and extend lifespan"""
        if not self.is_alive:
            return f"{self.name} is no longer alive. 💀"

        self.hunger = max(0, self.hunger - food_value)
        self.LIFESPAN += self.BASE_LIFESPAN_INCREASE  # Increase lifespan by hours
        self.last_fed = datetime.utcnow()
        return f"🍖 {self.name} has been fed! Hunger: {self.hunger}, Lifespan: {self.LIFESPAN} hours"

    def update_lifespan(self):
        """Update lifespan and apply hourly decay"""
        if not self.is_alive:
            return f"{self.name} is already gone. 💀"

        hours_since_last_fed = (datetime.utcnow() - self.last_fed).total_seconds() // 3600
        self.LIFESPAN -= hours_since_last_fed * self.DECAY_RATE * self.HOURLY_DECAY_MULTIPLIER  # Decay per hour

        # Increase hunger over time
        self.hunger = min(self.MAX_HUNGER, self.hunger + (hours_since_last_fed * self.HOURLY_HUNGER_INCREASE))

        if self.hunger >= self.MAX_HUNGER:
            self.LIFESPAN -= 2  # Reduce lifespan faster when starving

        if self.LIFESPAN <= 0:
            self.die()
            return f"💀 {self.name} has died due to neglect."

        return f"{self.name} is still alive. Hunger: {self.hunger}, Lifespan: {self.LIFESPAN} hours"

    def die(self):
        """Kill the pet"""
        self.is_alive = False
        return f"{self.name} has passed away. 💀"
    

    def __str__(self):
        return f"🐾 Pet {self.name} \nSpecies: { SpeciesType(self.type_id).name } \nElement: { ElementalType(self.ELEMENTAL_TYPE_ID).name } \nLevel: {self.LEVEL}, \nXP: {self.XP},\nHP: {self.MaxHP}, ATK: {self.MaxATK}, DEF: {self.MaxDEF}, SPEED: {self.MaxSPEED}, HUNGER: {self.hunger}"

    def train(self):
        """Train pet to gain XP and level up"""
        self.XP += 10
        if self.XP >= 100:
            self.LEVEL += 1
            self.XP = 0  # Reset XP after leveling up
            return f"{self.name} leveled up to {self.LEVEL}!"
        return f"{self.name} gained 10 XP! XP: {self.XP}/100"
