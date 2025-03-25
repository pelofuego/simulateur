# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 22:15:13 2025

@author: rene_
"""

import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, IntVar, StringVar, Radiobutton

# Dictionnaire complet des stats des troupes (ordre important pour la priorité de mort)
TROOP_STATS = [
    {'name': 'esclave', 'value': 1, 'pv': 4, 'attaque': 4, 'defense': 3},
    {'name': 'maitre esclave', 'value': 2, 'pv': 6, 'attaque': 6, 'defense': 4},
    {'name': 'jeunes soldates', 'value': 3, 'pv': 16, 'attaque': 8, 'defense': 7},
    {'name': 'soldates', 'value': 4, 'pv': 20, 'attaque': 11, 'defense': 10},
    {'name': 'soldates d\'élite', 'value': 5, 'pv': 26, 'attaque': 17, 'defense': 14},
    {'name': 'gardiennes', 'value': 6, 'pv': 25, 'attaque': 1, 'defense': 27},
    {'name': 'gardiennes d\'élites', 'value': 7, 'pv': 32, 'attaque': 1, 'defense': 35},
    {'name': 'tirailleuses', 'value': 8, 'pv': 12, 'attaque': 32, 'defense': 10},
    {'name': 'tirailleuses d\'élites', 'value': 9, 'pv': 15, 'attaque': 40, 'defense': 12},
    {'name': 'jeunes légionnaires', 'value': 10, 'pv': 40, 'attaque': 45, 'defense': 35},
    {'name': 'légionnaires', 'value': 11, 'pv': 55, 'attaque': 60, 'defense': 45},
    {'name': 'légionnaires d\'élites', 'value': 12, 'pv': 60, 'attaque': 65, 'defense': 50},
    {'name': 'jeunes tanks', 'value': 13, 'pv': 40, 'attaque': 80, 'defense': 1},
    {'name': 'tanks', 'value': 14, 'pv': 70, 'attaque': 140, 'defense': 1},
    {'name': 'tanks d\'élites', 'value': 15, 'pv': 80, 'attaque': 160, 'defense': 1}
]

# Création d'un dictionnaire rapide pour accès par nom
TROOP_DICT = {t['name']: t for t in TROOP_STATS}

TERRAIN_BONUS = {
    'Terrain de chasse': {'base': 0, 'per_level': 0},
    'Dôme': {'base': 5, 'per_level': 2.5},
    'Loge': {'base': 10, 'per_level': 5}
}

ALLIANCE_BONUS = {
    'Guerrier': {'attaque': 0.10, 'defense': 0.10, 'pv': 0},
    'Pacifique': {'attaque': 0, 'defense': 0, 'pv': 0.10},
    'Neutre': {'attaque': 0.05, 'defense': 0.05, 'pv': 0.05},
    'Pas d\'alliance': {'attaque': 0, 'defense': 0, 'pv': 0}
}

def parse_combat_text(text):
    pattern = r'(\d[\d ]*) ([a-zA-Zéèêëàâäôöûüç\' ]+?)(?=,|\n|$)'
    
    attack_section = re.search(r'Troupe en attaque *: *(.+?)(?:\n|$)', text, re.IGNORECASE)
    defense_section = re.search(r'Troupe en défense *: *(.+?)(?:\n|$)', text, re.IGNORECASE)

    result = {'attaque': {}, 'defense': {}}

    def parse_troops(text_section):
        troops = {}
        for match in re.finditer(pattern, text_section):
            quantity = int(match.group(1).replace(' ', ''))
            troop_type = match.group(2).strip().lower()
            if troop_type in TROOP_DICT:
                troops[troop_type] = quantity
        return troops

    if attack_section:
        result['attaque'] = parse_troops(attack_section.group(1))
    if defense_section:
        result['defense'] = parse_troops(defense_section.group(1))

    return result

def calculate_bonus(config, is_attacker=False):
    alliance_type = config['alliance_att'] if is_attacker else config['alliance_def']
    alliance_bonus = ALLIANCE_BONUS[alliance_type]
    
    # Bonus standards (sans alliance)
    mandibule = config['mandibule_att' if is_attacker else 'mandibule_def']
    carapace = config['carapace_att' if is_attacker else 'carapace_def']
    niveau_guerrier = min(config['niveau_guerrier_att' if is_attacker else 'niveau_guerrier_def'], 5)
    is_guerrier = config['is_guerrier_att' if is_attacker else 'is_guerrier_def']
    
    # Calcul des bonus
    bonus_attaque = 1 + (mandibule * 0.05) + (niveau_guerrier * 0.02 if is_guerrier else 0)
    bonus_defense = 1 + (mandibule * 0.05) + (niveau_guerrier * 0.02 if is_guerrier else 0)
    bonus_pv = 1 + (carapace * 0.05) + (niveau_guerrier * 0.02 if is_guerrier else 0)
    
    # Ajout bonus alliance (additif)
    bonus_attaque += alliance_bonus['attaque']
    bonus_defense += alliance_bonus['defense']
    bonus_pv += alliance_bonus['pv']
    
    # Bonus terrain pour défenseur
    if not is_attacker:
        terrain = config['terrain']
        niveau_terrain = config['niveau_terrain']
        terrain_bonus = TERRAIN_BONUS[terrain]
        bonus_pv *= 1 + (terrain_bonus['base'] + niveau_terrain * terrain_bonus['per_level']) / 100
    
    return {
        'attaque': bonus_attaque,
        'defense': bonus_defense,
        'pv': bonus_pv
    }

def calculate_stats(troupes, bonus):
    stats = {
        'total_pv': 0,
        'total_attaque_base': 0,  # Sans bonus
        'total_attaque_bonus': 0,  # Partie bonus seulement
        'total_defense_base': 0,   # Sans bonus
        'total_defense_bonus': 0,  # Partie bonus seulement
        'total_value': 0,
        'details': {}
    }
    
    for troop, quantity in troupes.items():
        base_stats = TROOP_DICT[troop]
        
        # Calcul des valeurs de base (sans bonus)
        pv_base = quantity * base_stats['pv']
        att_base = quantity * base_stats['attaque']
        def_base = quantity * base_stats['defense']
        
        # Calcul des valeurs avec bonus
        pv_total = pv_base * bonus['pv']
        att_total = att_base * bonus['attaque']
        def_total = def_base * bonus['defense']
        
        # Séparation base et bonus
        att_bonus = att_total - att_base
        def_bonus = def_total - def_base
        
        stats['total_pv'] += pv_total
        stats['total_attaque_base'] += att_base
        stats['total_attaque_bonus'] += att_bonus
        stats['total_defense_base'] += def_base
        stats['total_defense_bonus'] += def_bonus
        stats['total_value'] += quantity * base_stats['value']
        stats['details'][troop] = {
            'quantite': quantity,
            'pv': pv_total,
            'attaque_base': att_base,
            'attaque_bonus': att_bonus,
            'defense_base': def_base,
            'defense_bonus': def_bonus
        }
    
    return stats

def calculate_losses(troupes, degats, bonus_pv):
    pertes = {}
    degats_restants = degats
    
    # On parcourt les troupes dans l'ordre défini (les premières de la liste meurent en premier)
    for troop_info in TROOP_STATS:
        troop = troop_info['name']
        if troop in troupes and troupes[troop] > 0:
            pv_unite = troop_info['pv'] * bonus_pv
            nb_unites = troupes[troop]
            
            # Nombre d'unités qui peuvent être tuées avec les dégâts restants
            unites_tuees = min(nb_unites, int(degats_restants // pv_unite))
            
            if unites_tuees > 0:
                pertes[troop] = unites_tuees
                degats_restants -= unites_tuees * pv_unite
            
            if degats_restants <= 0:
                break
    
    return pertes

def format_number(num):
    return "{:,}".format(int(num)).replace(",", " ")

def simulate_combat(parsed_data, config):
    # Calcul des bonus pour chaque camp
    bonus_att = calculate_bonus(config, is_attacker=True)
    bonus_def = calculate_bonus(config, is_attacker=False)
    
    # Stats initiales
    stats_att = calculate_stats(parsed_data['attaque'], bonus_att)
    stats_def = calculate_stats(parsed_data['defense'], bonus_def)
    
    # Initialisation des résultats
    result = {
        'initial_stats': {
            'attaque': stats_att,
            'defense': stats_def
        },
        'tours': []
    }
    
    # Copie des troupes pour simulation
    troupes_att = parsed_data['attaque'].copy()
    troupes_def = parsed_data['defense'].copy()
    
    # Simulation des tours de combat
    max_tours = 10  # Limite de tours pour éviter les boucles infinies
    for tour in range(max_tours):
        # Calcul des stats actuelles
        current_stats_att = calculate_stats(troupes_att, bonus_att)
        current_stats_def = calculate_stats(troupes_def, bonus_def)
        
        # Si un camp n'a plus de troupes, on arrête
        if not troupes_att or not troupes_def:
            break
        
        # Attaque de l'attaquant
        degats_att_base = current_stats_att['total_attaque_base']
        degats_att_bonus = current_stats_att['total_attaque_bonus']
        pertes_def = calculate_losses(troupes_def, degats_att_base + degats_att_bonus, bonus_def['pv'])
        
        # Mise à jour des troupes défenseur
        for troop, nb_perdus in pertes_def.items():
            troupes_def[troop] -= nb_perdus
            if troupes_def[troop] <= 0:
                del troupes_def[troop]
        
        # Contre-attaque du défenseur
        degats_def_base = current_stats_def['total_defense_base']
        degats_def_bonus = current_stats_def['total_defense_bonus']
        pertes_att = calculate_losses(troupes_att, degats_def_base + degats_def_bonus, bonus_att['pv'])
        
        # Mise à jour des troupes attaquant
        for troop, nb_perdus in pertes_att.items():
            troupes_att[troop] -= nb_perdus
            if troupes_att[troop] <= 0:
                del troupes_att[troop]
        
        # Enregistrement des résultats du tour
        result['tours'].append({
            'degats_att_base': degats_att_base,
            'degats_att_bonus': degats_att_bonus,
            'pertes_def': sum(pertes_def.values()),
            'degats_def_base': degats_def_base,
            'degats_def_bonus': degats_def_bonus,
            'pertes_att': sum(pertes_att.values())
        })
        
        # Si aucun camp n'a fait de pertes ce tour, on arrête
        if sum(pertes_def.values()) == 0 and sum(pertes_att.values()) == 0:
            break
    
    # Stats finales
    result['final_troupes'] = {
        'attaque': troupes_att,
        'defense': troupes_def
    }
    
    return result

def update_terrain_level(*args):
    terrain = terrain_var.get()
    if terrain == "Terrain de chasse":
        niveau_terrain_spinbox.config(state='disabled')
    else:
        niveau_terrain_spinbox.config(state='normal')

def analyze_text():
    text = input_text.get("1.0", tk.END)
    if not text.strip():
        messagebox.showwarning("Attention", "Veuillez entrer un texte à analyser")
        return
    
    try:
        config = {
            'mandibule_att': mandibule_att_var.get(),
            'carapace_att': carapace_att_var.get(),
            'is_guerrier_att': is_guerrier_att_var.get(),
            'niveau_guerrier_att': niveau_guerrier_att_var.get(),
            'mandibule_def': mandibule_def_var.get(),
            'carapace_def': carapace_def_var.get(),
            'is_guerrier_def': is_guerrier_def_var.get(),
            'niveau_guerrier_def': niveau_guerrier_def_var.get(),
            'terrain': terrain_var.get(),
            'niveau_terrain': niveau_terrain_var.get() if terrain_var.get() != "Terrain de chasse" else 0,
            'alliance_att': alliance_att_var.get(),
            'alliance_def': alliance_def_var.get()
        }
        
        parsed_data = parse_combat_text(text)
        combat_result = simulate_combat(parsed_data, config)
        
        # Afficher les résultats
        result_text = "=== STATS AVANT LE COMBAT ===\n\n"
        
        # Stats attaquant
        result_text += "--- ATTAQUANT ---\n"
        result_text += f"Alliance: {config['alliance_att']}\n"
        for troop, details in combat_result['initial_stats']['attaque']['details'].items():
            result_text += (
                f"{troop.capitalize():<20} {format_number(details['quantite']):>10} unités | "
                f"PV: {format_number(details['pv'])} | "
                f"Att: {format_number(details['attaque_base'] + details['attaque_bonus'])} "
                f"(base: {format_number(details['attaque_base'])}, bonus: {format_number(details['attaque_bonus'])}) | "
                f"Def: {format_number(details['defense_base'] + details['defense_bonus'])} "
                f"(base: {format_number(details['defense_base'])}, bonus: {format_number(details['defense_bonus'])})\n"
            )
        result_text += (
            f"\nTOTAL: PV: {format_number(combat_result['initial_stats']['attaque']['total_pv'])} | "
            f"Att: {format_number(combat_result['initial_stats']['attaque']['total_attaque_base'] + combat_result['initial_stats']['attaque']['total_attaque_bonus'])} "
            f"(base: {format_number(combat_result['initial_stats']['attaque']['total_attaque_base'])}, bonus: {format_number(combat_result['initial_stats']['attaque']['total_attaque_bonus'])}) | "
            f"Def: {format_number(combat_result['initial_stats']['attaque']['total_defense_base'] + combat_result['initial_stats']['attaque']['total_defense_bonus'])} "
            f"(base: {format_number(combat_result['initial_stats']['attaque']['total_defense_base'])}, bonus: {format_number(combat_result['initial_stats']['attaque']['total_defense_bonus'])})\n\n"
        )
        
        # Stats défenseur
        result_text += "--- DÉFENSEUR ---\n"
        result_text += f"Alliance: {config['alliance_def']}\n"
        for troop, details in combat_result['initial_stats']['defense']['details'].items():
            result_text += (
                f"{troop.capitalize():<20} {format_number(details['quantite']):>10} unités | "
                f"PV: {format_number(details['pv'])} | "
                f"Att: {format_number(details['attaque_base'] + details['attaque_bonus'])} "
                f"(base: {format_number(details['attaque_base'])}, bonus: {format_number(details['attaque_bonus'])}) | "
                f"Def: {format_number(details['defense_base'] + details['defense_bonus'])} "
                f"(base: {format_number(details['defense_base'])}, bonus: {format_number(details['defense_bonus'])})\n"
            )
        result_text += (
            f"\nTOTAL: PV: {format_number(combat_result['initial_stats']['defense']['total_pv'])} | "
            f"Att: {format_number(combat_result['initial_stats']['defense']['total_attaque_base'] + combat_result['initial_stats']['defense']['total_attaque_bonus'])} "
            f"(base: {format_number(combat_result['initial_stats']['defense']['total_attaque_base'])}, bonus: {format_number(combat_result['initial_stats']['defense']['total_attaque_bonus'])}) | "
            f"Def: {format_number(combat_result['initial_stats']['defense']['total_defense_base'] + combat_result['initial_stats']['defense']['total_defense_bonus'])} "
            f"(base: {format_number(combat_result['initial_stats']['defense']['total_defense_base'])}, bonus: {format_number(combat_result['initial_stats']['defense']['total_defense_bonus'])})\n\n"
        )
        
        # Résultats des tours de combat
        result_text += "=== DÉROULEMENT DU COMBAT ===\n\n"
        for i, tour in enumerate(combat_result['tours'], 1):
            result_text += f"Tour {i}:\n"
            result_text += (
                f"Vous infligez {format_number(tour['degats_att_base'])} "
                f"(+ {format_number(tour['degats_att_bonus'])}) dégâts et vous tuez "
                f"{format_number(tour['pertes_def'])} ennemis\n"
            )
            result_text += (
                f"La défense riposte, vous infligeant {format_number(tour['degats_def_base'])} "
                f"(+ {format_number(tour['degats_def_bonus'])}) dégâts et tuant "
                f"{format_number(tour['pertes_att'])} unités.\n\n"
            )
        
        # Troupes survivantes
        result_text += "=== TROUPES SURVIVANTES ===\n\n"
        result_text += "Attaquant:\n"
        for troop, quantity in combat_result['final_troupes']['attaque'].items():
            result_text += f"- {troop.capitalize()}: {format_number(quantity)}\n"
        
        result_text += "\nDéfenseur:\n"
        for troop, quantity in combat_result['final_troupes']['defense'].items():
            result_text += f"- {troop.capitalize()}: {format_number(quantity)}\n"
        
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, result_text)
        
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue:\n{str(e)}")

# Création de l'interface
root = tk.Tk()
root.title("Analyseur de troupes avancé")
root.geometry("1400x1100")

style = ttk.Style()
style.configure('TFrame', background='#f0f0f0')
style.configure('TLabel', background='#f0f0f0')

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Cadre de configuration
config_frame = ttk.LabelFrame(main_frame, text="Configuration des bonus", padding=10)
config_frame.pack(fill=tk.X, pady=5)

# Configuration attaquant
att_frame = ttk.Frame(config_frame)
att_frame.pack(side=tk.LEFT, padx=10, expand=True)

ttk.Label(att_frame, text="Attaquant", font=('Helvetica', 10, 'bold')).pack()

mandibule_att_var = IntVar(value=0)
carapace_att_var = IntVar(value=0)
is_guerrier_att_var = tk.BooleanVar(value=False)
niveau_guerrier_att_var = IntVar(value=1)
alliance_att_var = StringVar(value="Pas d'alliance")

ttk.Label(att_frame, text="Niveau Mandibule:").pack()
ttk.Spinbox(att_frame, from_=0, to=50, textvariable=mandibule_att_var).pack()

ttk.Label(att_frame, text="Niveau Carapace:").pack()
ttk.Spinbox(att_frame, from_=0, to=50, textvariable=carapace_att_var).pack()

ttk.Checkbutton(att_frame, text="Spécialité Guerrier", variable=is_guerrier_att_var).pack()
ttk.Label(att_frame, text="Niveau Guerrier (max 5):").pack()
ttk.Spinbox(att_frame, from_=1, to=5, textvariable=niveau_guerrier_att_var).pack()

ttk.Label(att_frame, text="Type d'alliance:").pack()
ttk.Combobox(att_frame, textvariable=alliance_att_var, values=list(ALLIANCE_BONUS.keys())).pack()

# Configuration défenseur
def_frame = ttk.Frame(config_frame)
def_frame.pack(side=tk.LEFT, padx=10, expand=True)

ttk.Label(def_frame, text="Défenseur", font=('Helvetica', 10, 'bold')).pack()

mandibule_def_var = IntVar(value=0)
carapace_def_var = IntVar(value=0)
is_guerrier_def_var = tk.BooleanVar(value=False)
niveau_guerrier_def_var = IntVar(value=1)
alliance_def_var = StringVar(value="Pas d'alliance")

ttk.Label(def_frame, text="Niveau Mandibule:").pack()
ttk.Spinbox(def_frame, from_=0, to=50, textvariable=mandibule_def_var).pack()

ttk.Label(def_frame, text="Niveau Carapace:").pack()
ttk.Spinbox(def_frame, from_=0, to=50, textvariable=carapace_def_var).pack()

ttk.Checkbutton(def_frame, text="Spécialité Guerrier", variable=is_guerrier_def_var).pack()
ttk.Label(def_frame, text="Niveau Guerrier (max 5):").pack()
ttk.Spinbox(def_frame, from_=1, to=5, textvariable=niveau_guerrier_def_var).pack()

ttk.Label(def_frame, text="Type d'alliance:").pack()
ttk.Combobox(def_frame, textvariable=alliance_def_var, values=list(ALLIANCE_BONUS.keys())).pack()

# Configuration terrain
terrain_frame = ttk.Frame(config_frame)
terrain_frame.pack(side=tk.LEFT, padx=10, expand=True)

ttk.Label(terrain_frame, text="Terrain de combat", font=('Helvetica', 10, 'bold')).pack()

terrain_var = StringVar(value="Terrain de chasse")
niveau_terrain_var = IntVar(value=0)

for terrain in TERRAIN_BONUS:
    Radiobutton(terrain_frame, text=terrain, variable=terrain_var, value=terrain).pack(anchor='w')

ttk.Label(terrain_frame, text="Niveau du terrain:").pack()
niveau_terrain_spinbox = ttk.Spinbox(terrain_frame, from_=0, to=20, textvariable=niveau_terrain_var, state='disabled')
niveau_terrain_spinbox.pack()

terrain_var.trace('w', update_terrain_level)

# Cadre d'entrée
input_frame = ttk.LabelFrame(main_frame, text="Collez votre texte ici", padding=10)
input_frame.pack(fill=tk.BOTH, expand=True, pady=5)

input_text = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD, font=('Courier New', 10))
input_text.pack(fill=tk.BOTH, expand=True)

# Bouton d'analyse
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=5)
analyze_btn = ttk.Button(button_frame, text="Analyser", command=analyze_text)
analyze_btn.pack(pady=5)

# Cadre de résultats
output_frame = ttk.LabelFrame(main_frame, text="Résultats détaillés", padding=10)
output_frame.pack(fill=tk.BOTH, expand=True, pady=5)

output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=('Courier New', 10))
output_text.pack(fill=tk.BOTH, expand=True)

# Exemple de texte par défaut
default_text = """Troupe en attaque : 87 596 Jeunes soldates, 8 466 Soldates, 1 295 Soldates d'élite
Troupe en défense : 27 814 Jeunes soldates, 15 218 Soldates, 11 551 Soldates d'élite"""
input_text.insert(tk.END, default_text)

root.mainloop()