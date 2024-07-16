from flask import Flask, request, jsonify, render_template
import shutil
import os
import pandas as pd
from character import create_or_update_character, get_character, get_rank_attributes, get_battle_character
from battle import battle_round, save_character, update_cooldowns
import webbrowser
from threading import Timer

app = Flask(__name__)
players = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create_or_update_character', methods=['POST'])
def api_create_or_update_character():
    data = request.form
    name = data['name']
    rank = data['rank']
    strength = data.get('strength')
    intelligence = data.get('intelligence')
    agility = data.get('agility')
    armor = data.get('armor')
    health = data.get('health')

    skills = {}
    for key in data.keys():
        if key.startswith('skill_name_'):
            index = key.split('_')[-1]
            skill_name = data[key]
            skill_cd = data.get(f'skill_cd_{index}')
            skills[skill_name] = int(skill_cd)

    create_or_update_character(
        name=name,
        rank=rank,
        strength=strength,
        intelligence=intelligence,
        agility=agility,
        armor=armor,
        health=health,
        skills=skills
    )
    return jsonify({"message": "角色创建成功。"})

@app.route('/get_character', methods=['GET'])
def api_get_character():
    name = request.args.get('name')
    if not name:
        return jsonify({"message": "Character name is required."}), 400

    character = get_character(name)
    if character is not None:
        return jsonify(character)
    else:
        return jsonify({"message": "Character not found."}), 404

@app.route('/add_player', methods=['POST'])
def add_player():
    name = request.form['name']
    data_file_path = f"data/{name}.csv"
    battle_file_path = f"battle_system/{name}.csv"

    if os.path.exists(data_file_path):
        shutil.copy(data_file_path, battle_file_path)
        character = get_character(name)
        if character:
            players.append(character)
            return jsonify({"message": f"角色‘ {name } ’添加成功。"})
        else:
            return jsonify({"message": "该角色未创建。"}), 404
    else:
        return jsonify({"message": "该角色未创建。"}), 404

@app.route('/start_battle', methods=['POST'])
def start_battle():
    attacker_name = request.form['attacker']
    defender_name = request.form['defender']
    action = request.form['action']
    selected_skill = request.form.get('selected_skill', None)
    dice_value = int(request.form['dice_value'])
    distance = 'distance' in request.form
    aoe = 'aoe' in request.form
    hurt = 'hurt' in request.form
    sneak_attack = 'sneak_attack' in request.form
    defend = 'defend' in request.form  # New checkbox value
    
    defined_damage = request.form.get('defined-damage')
    damage_reduce = request.form.get('damage_reduce')
    strength = request.form.get('strength')
    intelligence = request.form.get('intelligence')
    agility = request.form.get('agility')
    armor = request.form.get('armor')
    health = request.form.get('health')

    attacker = get_battle_character(attacker_name)
    defender = get_battle_character(defender_name)

    if attacker is None or not attacker or defender is None or not defender:
        return jsonify({"message": "该角色未创建或未加入战斗。"}), 400
    
    result = battle_round(attacker, defender, action, dice_value, distance, aoe, hurt, sneak_attack, defined_damage, damage_reduce, selected_skill, defend)
    
    print("Battle round result:\n", result)
    # 更新角色属性
    if strength:
        defender['Strength'] = float(strength)
    if intelligence:
        defender['Intelligence'] = float(intelligence)
    if agility:
        defender['Agility'] = float(agility)
    if armor:
        defender['Armor'] = float(armor)
    if health:
        defender['Health'] = float(health)
    
    save_character(defender)
    save_character(attacker)  # Save attacker as well

    return jsonify({
        "message": result["message"],
        "damage": result.get('damage', 0),
        "attacker": result['attacker'],
        "defender": result['defender'],
    })

@app.route('/next_round', methods=['POST'])
def next_round():
    # for player_name in [player['Name'] for player in players]:
    #     character = get_battle_character(player_name)
    #     update_cooldowns(character)
    #     save_character(character)  # Save each player's updated state
    return jsonify({"message": "进入下一回合。"})

@app.route('/end_battle', methods=['POST'])
def end_battle():
    global players
    players = []
    for file_name in os.listdir('battle_system'):
        if file_name.endswith('.csv'):
            os.remove(os.path.join('battle_system', file_name))
    return jsonify({"message": "战斗结束。所有角色已移除。"})

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True)
