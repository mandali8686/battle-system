import pandas as pd
import os

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
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

def battle_round(attacker, defender, action, dice_value, distance, aoe, hurt, sneak_attack, defined_damage, damage_reduce):
    diff_df = get_diff_attributes()
    
    success_rate = 75 if not distance else 50
    
    if action == 'skill':
        print("Skill Attacking")
        diff = int(attacker['Intelligence']) - int(defender['Intelligence'])
        ref_col = "Intelligence_diff"
        success_col = 'Skill_success'
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
    
    # Calculate sneak attack factor
    sneak_attack_factor = 0.5 if sneak_attack else 0
    
    if aoe:
        skill_damage = (1.45 + sneak_attack_factor) * 0.75 * damage_reduction_factor * sneak_attack_factor * int(attacker['Strength'])
    else:
        skill_damage = (1.45 + sneak_attack_factor) * damage_reduction_factor * int(attacker['Strength'])
    
    if fail_rate <= 0 or dice_value > fail_rate:
        print("!!!Attack Success!!!")
        
        if hurt:
            damage = (1+sneak_attack_factor)* damage_reduction_factor* int(attacker['Strength']) if action != 'skill' else skill_damage
        else: 
            damage = 0
        
        if defined_damage:
            defined_damage = float(defined_damage)
        
        defender['Health'] -= defined_damage if defined_damage else damage
        
        save_character(defender)  # 保存更新的防守者状态
        save_character(attacker)  # 保存更新的攻击者状态
        
        return {
            "success": True,
            "message": "判定成功",
            "attacker": attacker.to_dict(),
            "defender": defender.to_dict(),
            "damage": damage if not defined_damage else defined_damage
        }
    else:
        print("...Attack Fail...")
        save_character(defender)  # 保存更新的防守者状态
        save_character(attacker)  # 保存更新的攻击者状态
        return {
            "success": False,
            "message": "判定失败",
            "attacker": attacker.to_dict(),
            "defender": defender.to_dict()
        }
