import pandas as pd
import os
import numpy as np

def create_or_update_character(name, rank, strength=None, intelligence=None, agility=None, armor=None, health=None, skills=None):
    rank_attributes = get_rank_attributes(rank)
    
    # 如果用户没有提供某个属性的值，则使用rank.csv中的默认值
    strength = float(strength) if strength is not None and strength != "" else rank_attributes['Strength']
    intelligence = float(intelligence) if intelligence is not None and intelligence != "" else rank_attributes['Intelligence']
    agility = float(agility) if agility is not None and agility != "" else rank_attributes['Agility']
    armor = float(armor) if armor is not None and armor != "" else rank_attributes['Armor']
    health = float(health) if health is not None and health != "" else rank_attributes['Health']

    file_path = f"data/{name}.csv"
    
    data = {
        'Name': [name],
        'Rank': [rank],
        'Strength': [strength],
        'Intelligence': [intelligence],
        'Agility': [agility],
        'Armor': [armor],
        'Health': [health]
    }
    
    if skills:
        for skill_name, skill_cd in skills.items():
            data[skill_name] = [skill_cd]
    
    df = pd.DataFrame(data)
    
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        df = pd.concat([existing_df, df]).drop_duplicates(subset=['Name'], keep='last')
    
    df.to_csv(file_path, index=False)
    print(f"Character {name} has been created/updated.")

def get_character(name):
    file_path = f"data/{name}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        character = df.iloc[0].to_dict()
        # Convert any numpy data types to native Python types
        for key in character:
            if isinstance(character[key], (np.int64, np.float64)):
                character[key] = character[key].item()
        skills = {col: character[col] for col in character.keys() if col not in ['Name', 'Rank', 'Strength', 'Intelligence', 'Agility', 'Armor', 'Health']}
        
        character['Skills'] = skills
        print(character)
        return character
    else:
        print(f"No character found with the name {name}.")
        return {}

def get_battle_character(name):
    file_path = f"battle_system/{name}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        character = df.iloc[0].to_dict()
        # Convert any numpy data types to native Python types
        for key in character:
            if isinstance(character[key], (np.int64, np.float64)):
                character[key] = character[key].item()
        skills = {col: character[col] for col in character.keys() if col not in ['Name', 'Rank', 'Strength', 'Intelligence', 'Agility', 'Armor', 'Health']}
        character['Skills'] = skills
        return character
    else:
        print(f"No character found with the name {name}.")
        return {}

def get_rank_attributes(rank):
    rank_file_path = "reference/rank.csv"
    rank_df = pd.read_csv(rank_file_path)
    rank_data = rank_df[rank_df['Rank'] == int(rank)].iloc[0]
    return {
        'Strength': rank_data['Strength'],
        'Intelligence': rank_data['Intelligence'],
        'Agility': rank_data['Agility'],
        'Armor': rank_data['Armor'],
        'Health': rank_data['Health']
    }
