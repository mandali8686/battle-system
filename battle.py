import pandas as pd
import os
import numpy as np

def get_diff_attributes():
    diff_file_path = "reference/diff.csv"
    diff_df = pd.read_csv(diff_file_path)
    
    # 确保相关列是数值类型
    num_cols = ['Armor', 'Damage_reduce', 'Intelligence_diff', 'Skill_success', 'Agility_diff', 'Hit_success']
    diff_df[num_cols] = diff_df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    return diff_df

def save_character(character):
    file_path = f"battle_system/{character['Name']}.csv"
    data = {
        'Name': [character['Name']],
        'Rank': [character['Rank']],
        'Strength': [character['Strength']],
        'Intelligence': [character['Intelligence']],
        'Agility': [character['Agility']],
        'Armor': [character['Armor']],
        'Health': [character['Health']]
    }
    if 'Skills' in character:
        for skill, full_cd in character['Skills'].items():
            data[skill] = [full_cd]
            data[f"{skill}_current_cd"] = [character.get(f"{skill}_current_cd", full_cd)]
            data[f"{skill}_used"] = [character.get(f"{skill}_used", False)]
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

def get_battle_character(name):
    file_path = f"battle_system/{name}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        character = df.iloc[0].to_dict()
        skills = {col: character[col] for col in character.keys() if col not in ['Name', 'Rank', 'Strength', 'Intelligence', 'Agility', 'Armor', 'Health'] and not col.endswith('_current_cd') and not col.endswith('_used')}
        for skill in skills:
            character[skill] = int(character[skill])
            character[f"{skill}_current_cd"] = int(character.get(f"{skill}_current_cd", character[skill]))
            character[f"{skill}_used"] = character.get(f"{skill}_used", False) == 'True'
        character['Skills'] = skills
        return character
    else:
        print(f"No character found with the name {name}.")
        return None

round_counter = 0

def battle_round(attacker, defender, action, dice_value, distance, aoe, hurt, sneak_attack, defined_damage, damage_reduce, selected_skill='', defend=False):
    global round_counter
    diff_df = get_diff_attributes()
    
    success_rate = 75 if not distance else 50

    if action == 'skill' and selected_skill:
        print(f"Skill Attacking with {selected_skill}")
        full_cd = attacker['Skills'][selected_skill]
        print(f"{selected_skill}_current_cd")
        current_cd = attacker.get(f"{selected_skill}_current_cd", full_cd)
        skill_used = attacker.get(f"{selected_skill}_used", False)
        if not skill_used:
            diff = int(attacker['Intelligence']) - int(defender['Intelligence'])
            ref_col = "Intelligence_diff"
            success_col = 'Skill_success'
            attacker[f"{selected_skill}_current_cd"] = full_cd  # Set the initial cooldown
            attacker[f"{selected_skill}_used"] = True  # Mark the skill as used
        elif skill_used and current_cd > 0:
            return {"message": f"技能 {selected_skill} 冷却中。", "attacker": attacker, "defender": defender}
        else:
            attacker[f"{selected_skill}_current_cd"] = full_cd  # Reset skill cooldown after use
    else:
        print("Attacking")
        diff = int(attacker['Agility']) - int(defender['Agility'])
        ref_col = "Agility_diff"
        success_col = 'Hit_success'
    
    # Debugging prints
    print("Difference:", abs(diff))
    
    success_change = diff_df[diff_df[ref_col] == abs(diff)][success_col].values
    print("Success change:", success_change)
    
    if success_change.size > 0:
        success_change = success_change[0]
        success_rate += success_change if diff > 0 else -success_change
    
    if sneak_attack:
        success_rate += 20
    
    print("Updated success rate:", success_rate)
    
    fail_rate = 100 - success_rate
    
    # Calculate damage reduction factor
    damage_reduction_factor = 1
    if damage_reduce:
        damage_reduce = float(damage_reduce)
        damage_reduction_factor -= damage_reduce / 100
    else:
        # If damage_reduce is not provided, calculate default damage reduction based on armor difference
        armor_diff = abs(attacker['Armor'] - defender['Armor'])
        default_damage_reduce = diff_df[diff_df['Armor'] == armor_diff]['Damage_reduce'].values
        if default_damage_reduce.size > 0:
            damage_reduction_factor -= default_damage_reduce[0] / 100

    # Calculate sneak attack factor
    sneak_attack_factor = 0.5 if sneak_attack else 0

    # Calculate defend factor
    defend_factor = 0.5 if defend else 1
    
    if aoe:
        skill_damage = (1.45 + sneak_attack_factor) * 0.75 * damage_reduction_factor * sneak_attack_factor * int(attacker['Strength'])
    else:
        skill_damage = (1.45 + sneak_attack_factor) * damage_reduction_factor * int(attacker['Strength'])
    
    if fail_rate <= 0 or dice_value > fail_rate:
        print("!!!Attack Success!!!")
        
        if hurt:
            damage = (1+sneak_attack_factor) * damage_reduction_factor * int(attacker['Strength']) if action != 'skill' else skill_damage
            damage *= defend_factor  # Apply defend factor
        else: 
            damage = 0
        
        if defined_damage:
            defined_damage = float(defined_damage)
            damage = defined_damage
        
        defender['Health'] -= damage
        
        save_character(defender)  # 保存更新的防守者状态
        save_character(attacker)  # 保存更新的攻击者状态
        
        return {
            "success": True,
            "message": "判定成功",
            "attacker": attacker,
            "defender": defender,
            "damage": damage
        }
    else:
        print("...Attack Fail...")
        save_character(defender)  # 保存更新的防守者状态
        save_character(attacker)  # 保存更新的攻击者状态
        return {
            "success": False,
            "message": "判定失败",
            "attacker": attacker,
            "defender": defender
        }

def update_cooldowns(character):
    global round_counter
    round_counter += 1
    if round_counter % 2 == 0:  # Only update cooldowns every two rounds
        for skill in character['Skills']:
            full_cd = character[skill]
            current_cd = character.get(f"{skill}_current_cd", full_cd)
            skill_used = character.get(f"{skill}_used", False)
            if skill_used:  # If the skill has been used
                character[f"{skill}_current_cd"] = max(0, current_cd - 1)  # Decrement cooldown
                if character[f"{skill}_current_cd"] == 0:
                    character[f"{skill}_used"] = False  # Reset the skill used flag when cooldown reaches zero
