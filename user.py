from flask_login import UserMixin
from db import db
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
from flask_pymongo import wrappers

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user_data = db.users.find_one({"_id": user_id})
        if not user_data:
            return None
        return User(
            id_=str(user_data["_id"]),
            name=user_data["name"],
            email=user_data["email"],
            profile_pic=user_data["profile_pic"],
        )

    @staticmethod
    def create(id_, name, email, profile_pic):
        try:
            db.users.insert_one({
                "_id": id_,
                "name": name,
                "email": email,
                "profile_pic": profile_pic,
            })
        except DuplicateKeyError as e:
            # Handle the case where the user already exists
            return None
        return User(id_, name, email, profile_pic)
    
def valid_id(name: str) -> str:
    return name.replace(" ", "-").lower()

class Pinpoint:
    #created to define pinpoints on the map and update db
    def __init__(self, name, lat, long, description):
        self.id = valid_id(name)
        self.lat = lat
        self.long = long
        self.name = name
        self.description = description

    @staticmethod
    def get(pinpoint_id):
        pinpoint_data = db.mappoints.find_one({"_id": pinpoint_id})
        if not pinpoint_data:
            return None
        return Pinpoint(
            name=pinpoint_data["name"],
            lat=pinpoint_data["lat"],
            long=pinpoint_data["long"],
            description=pinpoint_data["description"]
        )
    
    @staticmethod
    def create(name, lat, long, description):
        try:
            db.mappoints.insert_one({
                "_id": valid_id(name),
                "name": name,
                "lat": lat,
                "long": long,
                "description": description,
            })
        except OperationFailure as e:
            # Handle the case where the pinpoint already exists
            return None
        return Pinpoint(name, lat, long, description)

    @staticmethod
    def getall() -> list:
        mappoints : wrappers.Collection = db.mappoints
        pinpoints = list(mappoints.find())
        return pinpoints