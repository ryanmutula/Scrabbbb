from flask import Blueprint,jsonify,request
from flask_jwt_extended import create_access_token,JWTManager
from . import db,bcrypt
from datetime import timedelta,datetime,timezone
from .models import Member,Game
import json
import random

auth_blueprint=Blueprint('auth',__name__)

@auth_blueprint.route("/signup",methods=["POST"])
def signup():
    body=request.get_json()
    name=body.get('name')
    email=body.get('email')
    password=body.get('password')

    ## Validation
    if not email or not password or not name:
        return jsonify({'message':"Required field missing"}),400
    
    if len(email)<4:
        return jsonify({'message':"Email too short"}),400
    
    if len(name)<4:
        return jsonify({'message':"Name too short"}),400
    
    if len(password)<4:
        return jsonify({'message':"Password too short"}),400
    
    existing_member=Member.query.filter_by(email=email).first()

    if existing_member:
        return jsonify({'message':f"Email already in use {email}"}),400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
    
    member=Member(name=name,email=email,password=hashed_password)
    db.session.add(member)
    db.session.commit()
    return jsonify({"message":"Sign up success"}),201
    
@auth_blueprint.route("/login",methods=["POST"])
def login():
    body=request.get_json()
    email=body.get('email')
    password=body.get('password')

       
    if not email or not password:
        return jsonify({'message':"Required field missing"}),400
    user=Member.query.filter_by(email=email).first()

 
    if not user:
        return jsonify({'message':"User not found"}),400
    
    
    pass_ok=bcrypt.check_password_hash(user.password.encode('utf-8'),password)
    
    if not pass_ok:
        return jsonify({"message":"Invalid password"}),401

    expires=datetime.utcnow()+timedelta(hours=24)
   
    access_token=create_access_token(identity={"id":user.id,"name":user.name,"role":"cats and dogs"},expires_delta=(expires-datetime.utcnow()))
   
    if not user.game:
        member_id = user.id
        board = [[" " for _ in range(15)] for _ in range(15)]
        special_tiles = {
            (7, 7): "  X ", (0, 0): " TW ", (0, 3): " DL ", (0, 7): " TW ", (0, 11): " DL ", (0, 14): " TW ",
            (1, 1): " DW ", (1, 5): " TL ", (1, 9): " TL ", (1, 13): " DW ", (2, 2): " DW ", (2, 6): " DL",
            (2, 8): " DL ", (2, 12): " DW ", (3, 0): " DL ", (3, 3): " DW ", (3, 7): " DL ", (3, 11): " DW ",
            (3, 14): " DL ", (4, 4): " DW ", (4, 10): " DW ", (5, 1): " TL ", (5, 5): " TL ", (5, 9): " TL ",
            (5, 13): " TL ", (6, 2): " DL", (6, 6): " DL ", (6, 8): " DL ", (6, 12): " DL ", (7, 0): " TW ",
            (7, 3): " DL ", (7, 11): " DL ", (7, 14): " TW ", (8, 2): " DL ", (8, 6): " DL ", (8, 8): " DL ",
            (8, 12): " DL ", (9, 1): " TL ", (9, 5): " TL ", (9, 9): " TL", (9, 13): " TL ", (10, 4): " DW ",
            (10, 10): " DW ", (11, 0): " DL ", (11, 3): " DW ", (11, 7): " DL ", (11, 11): " DW ", (11, 14): " DL ",
            (12, 2): " DW ", (12, 6): " DL ", (12, 8): " DL ", (12, 12): " DW ", (13, 1): " DW ", (13, 5): " TL",
            (13, 9): " TL ", (13, 13): " DW ", (14, 0): " TW ", (14, 3): " DL", (14, 7): " TW ", (14, 11): " DL ",
            (14, 14): " TW "
        }

        for (row, col), tile in special_tiles.items():
            board[row][col] = tile

        letter_no = {
            'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12,
            'F': 2, 'G': 3, 'H': 2, 'I': 9, 'J': 1,
            'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8,
            'P': 2, 'Q': 1, 'R': 6, 'S': 4, 'T': 6,
            'U': 4, 'V': 2, 'W': 2, 'X': 1, 'Y': 2, 'Z': 1
        }
        letter_bag = []

        for letter, count in letter_no.items():
            letter_bag.extend([letter] * count)
        random.shuffle(letter_bag)
        player_rack = [letter_bag.pop() for _ in range(7)]

        board_json = json.dumps(board)
        tile_bag_json = json.dumps(letter_bag)
        player_rack_json = json.dumps(player_rack)
        print("Initial board state:", board_json)
        print("Initial tile bag:", tile_bag_json)
        print("Player rack:", player_rack_json)
        game = Game(
            member_id=member_id,
            board=board_json,
            tile_bag=tile_bag_json,
            player_rack=player_rack_json
        )

        db.session.add(game)
        db.session.commit()

        return jsonify({'user': user.details(), 'token': access_token})   


