from enum import Enum

class ElementalType(Enum):
    WATER = 0
    GRASS = 1
    FIRE = 2

class SpeciesType(Enum):
    DOG = 0


class Pet:
    def __init__(self, pet_id, user_id, name, type_id, birthday, is_alive, hunger, 
                 HP_IV, ATK_IV, DEF_IV, SPEED_IV, LEVEL, LIFESPAN, XP, ELEMENTAL_TYPE_ID, 
                 HP, ATK, DEF, SPEED, DECAY_RATE):
        self.pet_id = pet_id
        self.user_id = user_id
        self.name = name
        self.type_id = type_id
        self.birthday = birthday
        self.is_alive = bool(is_alive)
        self.hunger = hunger
        self.HP_IV = HP_IV
        self.ATK_IV = ATK_IV
        self.DEF_IV = DEF_IV
        self.SPEED_IV = SPEED_IV
        self.LEVEL = LEVEL
        self.LIFESPAN = LIFESPAN
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

    def __str__(self):
        return f"🐾 Pet {self.name} \nSpecies: { SpeciesType(self.type_id).name } \nElement: { ElementalType(self.ELEMENTAL_TYPE_ID).name } \nLevel: {self.LEVEL}, \nXP: {self.XP},\nHP: {self.MaxHP}, ATK: {self.MaxATK}, DEF: {self.MaxDEF}, SPEED: {self.MaxSPEED}, HUNGER: {self.hunger}"

    def feed(self, food_value=5):
        """Feeds the pet to reduce hunger"""
        self.hunger = max(0, self.hunger - food_value)
        return f"{self.name} has been fed! Hunger: {self.hunger}"

    def train(self):
        """Train pet to gain XP and level up"""
        self.XP += 10
        if self.XP >= 100:
            self.LEVEL += 1
            self.XP = 0  # Reset XP after leveling up
            return f"{self.name} leveled up to {self.LEVEL}!"
        return f"{self.name} gained 10 XP! XP: {self.XP}/100"
