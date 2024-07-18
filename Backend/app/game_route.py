import random
from collections import Counter
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Game
from . import db
import json

print("WELCOME TO SCRABBLE, GOOD LUCK")

def load_dictionary(file_path):
    with open(file_path, 'r') as file:
        words = file.read().splitlines()
    return [word.upper() for word in words]

dictionary = load_dictionary('dictionary.txt')

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

letter_points = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1,
    'F': 4, 'G': 2, 'H': 4, 'I': 1, 'J': 8,
    'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1,
    'P': 3, 'Q': 10, 'R': 1, 'S': 1, 'T': 1,
    'U': 1, 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10
}

letter_no = {
    'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12,
    'F': 2, 'G': 3, 'H': 2, 'I': 9, 'J': 1,
    'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8,
    'P': 2, 'Q': 1, 'R': 6, 'S': 4, 'T': 6,
    'U': 4, 'V': 2, 'W': 2, 'X': 1, 'Y': 2, 'Z': 1
}

def create_board():
    board = [[" " for _ in range(15)] for _ in range(15)]
    for (row, col), tile in special_tiles.items():
        board[row][col] = tile
    return board

def draw_tiles(rack, letter_bag):
    while len(rack) < 7 and letter_bag:
        rack.append(letter_bag.pop())

def can_form_word(word, rack):
    rack_counter = Counter(rack)
    word_counter = Counter(word)
    for letter, count in word_counter.items():
        if rack_counter[letter] < count:
            return False
    return True

def display_board(board):
    cell_width = 4

    header = "     " + " | ".join(f"{i:<{cell_width}}" for i in range(15)) + " |"
    separator = "  " + "+".join("-" * (cell_width + 2) for _ in range(15)) + "+"

    board_str = header + "\n" + separator + "\n"

    for i in range(15):
        row_header = f"{i:<2} | "
        row_content = " | ".join(f"{board[i][j]:<{cell_width}}" for j in range(15))
        row_str = row_header + row_content + " |"

        board_str += row_str + "\n"
        board_str += separator + "\n"

    return board_str

game_blueprint = Blueprint('game', __name__)

@game_blueprint.route("/game/another", methods=["GET"])
@jwt_required()
def another():
    current_user = get_jwt_identity()
    print(current_user)
    return "Another one"

@game_blueprint.route("/game/board", methods=["GET"])
@jwt_required()
def get_board():
    current_user = get_jwt_identity()
    print(current_user)
    game = Game.query.filter_by(member_id=current_user['id']).first()
    print(game)
    if not game:
        return jsonify({'message': "Game not found"}), 400
    board = json.loads(game.board)
    return jsonify({'message': f"Hi {current_user['alias']} this is your board", 'board': board})

@game_blueprint.route("/game/make-move", methods=["PUT"])
@jwt_required()
def make_move():
    body = request.get_json()
    word = body.get("word")
    row = body.get("row")
    col = body.get("col")
    direction = body.get("direction").upper()

    if not word or row is None or col is None or not direction:
        return jsonify({"message": "Required fields missing"}), 400

    current_user = get_jwt_identity()
    game = Game.query.filter_by(member_id=current_user['id']).first()
    if not game:
        return jsonify({'message': "Game not found"}), 400

    board = json.loads(game.board)
    player_rack = json.loads(game.player_rack)

    if not can_form_word(word, player_rack):
        return jsonify({"message": "Invalid move: word cannot be formed from your rack"}), 400

    valid_move = True
    if direction == 'H':
        if col + len(word) > 15:
            valid_move = False
        for i, letter in enumerate(word):
            if board[row][col + i] not in [" ", letter]:
                valid_move = False
                break
    elif direction == 'V':
        if row + len(word) > 15:
            valid_move = False
        for i, letter in enumerate(word):
            if board[row + i][col] not in [" ", letter]:
                valid_move = False
                break
    else:
        return jsonify({"message": "Invalid direction"}), 400

    if not valid_move:
        return jsonify({"message": "Invalid move: word cannot be placed on the board"}), 400

    if direction == 'H':
        for i, letter in enumerate(word):
            board[row][col + i] = letter
            player_rack.remove(letter)
    elif direction == 'V':
        for i, letter in enumerate(word):
            board[row + i][col] = letter
            player_rack.remove(letter)

    # Draw new tiles to replace the ones used
    letter_bag = json.loads(game.tile_bag)
    draw_tiles(player_rack, letter_bag)

    # Update the game state
    game.board = json.dumps(board)
    game.player_rack = json.dumps(player_rack)
    game.tile_bag = json.dumps(letter_bag)
    db.session.commit()

    return jsonify({'board': display_board(board), "message": "Move made successfully"})

@game_blueprint.route("/game/possible-moves", methods=["GET"])
@jwt_required()
def possible_moves():
    current_user = get_jwt_identity()
    game = Game.query.filter_by(member_id=current_user['id']).first()
    if not game:
        return jsonify({'message': "Game not found"}), 400

    board = json.loads(game.board)
    player_rack = json.loads(game.player_rack)

    possible_moves = []

    for word in dictionary:
        if can_form_word(word, player_rack):
            for row in range(15):
                for col in range(15):
                    if col + len(word) <= 15 and all(board[row][col + i] in [" ", word[i]] for i in range(len(word))):
                        possible_moves.append({"word": word, "row": row, "col": col, "direction": "H"})
                    if row + len(word) <= 15 and all(board[row + i][col] in [" ", word[i]] for i in range(len(word))):
                        possible_moves.append({"word": word, "row": row, "col": col, "direction": "V"})

    return jsonify({'possible_moves': possible_moves}), 200

@game_blueprint.route("/game/new-game", methods=["POST"])
@jwt_required()
def new_game():
    current_user = get_jwt_identity()
    game = Game.query.filter_by(member_id=current_user['id']).first()
    if game:
        return jsonify({'message': "Game already exists"}), 400

    # Create a new Scrabble board and initialize it with special tiles
    board = create_board()

    # Initialize tile bag and player rack
    letter_bag = []
    for letter, count in letter_no.items():
        letter_bag.extend([letter] * count)
    random.shuffle(letter_bag)
    player_rack = [letter_bag.pop() for _ in range(7)]

    # Convert the board, tile bag, and player rack to JSON strings
    board_json = json.dumps(board)
    tile_bag_json = json.dumps(letter_bag)
    player_rack_json = json.dumps(player_rack)

    # Create a new Game object with the initial state
    game = Game(
        member_id=current_user['id'],
        board=board_json,
        tile_bag=tile_bag_json,
        player_rack=player_rack_json
    )

    db.session.add(game)
    db.session.commit()

    return jsonify({'message': "New game created", 'board': board, 'player_rack': player_rack})

