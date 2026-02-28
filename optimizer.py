import sqlite3
import pandas as pd
import random

# --- CONFIGURATION ---
SCALE_REQUIREMENTS = {
    1: {"lead": 1, "support": 0}, 
    2: {"lead": 1, "support": 2},
    3: {"lead": 1, "support": 3},
    4: {"lead": 1, "support": 4}
}

# Mapping semesters to Experience Points (1=New, 3=Senior)
SEM_MAP = {
    'S23': 3.0, 'F23': 3.0, 
    'S24': 3.0, 'F24': 2.0, 
    'S25': 2.0, 'F25': 1.0,
    'S26': 1.0, 'F26': 0.0  # Reserves
}

def get_optimized_team():
    print("--- 🤖 AIRA True-Shuffle Optimizer ---")
    
    # 1. Inputs
    target_category = input("Enter Program Category: ").strip()
    target_scale = int(input("Enter Program Scale (1-4): "))
    target_month = int(input("Enter Month (1-12): "))

    conn = sqlite3.connect('data/aria_main.db')
    
    # 2. Load Data
    ra_df = pd.read_sql_query("SELECT ra_id, name, semester_joined FROM RA", conn)
    history_df = pd.read_sql_query('''
        SELECT a.ra_id, p.category, p.program_date, p.program_id 
        FROM assignments a 
        JOIN programs p ON a.program_id = p.program_id
    ''', conn)
    
    collab_df = pd.read_sql_query('''
        SELECT a1.ra_id AS ra1, a2.ra_id AS ra2, COUNT(*) as shared_count
        FROM assignments a1
        JOIN assignments a2 ON a1.program_id = a2.program_id
        WHERE a1.ra_id != a2.ra_id
        GROUP BY a1.ra_id, a2.ra_id
    ''', conn)
    conn.close()

    # 3. Scale Flexibility
    reqs = SCALE_REQUIREMENTS.get(target_scale).copy()
    if target_scale == 1:
        if input("Is this (1) Solo or (2) Duo? ") == "2": 
            reqs["support"] = 1
    
    total_needed = reqs["lead"] + reqs["support"]

    # 4. Preliminary Pool (Equal Opportunity)
    pool = []
    for _, ra in ra_df.iterrows():
        exp_val = SEM_MAP.get(ra['semester_joined'], 1.0)
        
        # RESTRICTION: NO RESERVES (F26)
        if exp_val == 0.0:
            continue

        ra_history = history_df[history_df['ra_id'] == ra['ra_id']]
        
        # RESTRICTION: Monthly Cap (Max 2)
        if ra_history[pd.to_datetime(ra_history['program_date']).dt.month == target_month].shape[0] >= 2:
            continue

        # TRUE RANDOM START: Everyone gets exactly 10 base tickets
        pool.append({
            'id': ra['ra_id'],
            'name': ra['name'],
            'exp': exp_val,
            'base_weight': 10 
        })

    # 5. The Weighted Shuffle (Social Rotation Logic)
    selected_team = []
    
    for i in range(total_needed):
        if not pool: break
        
        for candidate in pool:
            penalty = 0
            for member in selected_team:
                # Check how many times they've worked together across ALL history
                match = collab_df[(collab_df['ra1'] == candidate['id']) & (collab_df['ra2'] == member['id'])]
                if not match.empty:
                    # HEAVY PENALTY for repeat pairings (3 points per past collaboration)
                    penalty += int(match['shared_count'].iloc[0]) * 3
            
            # The more they've worked together, the fewer 'tickets' they have left
            candidate['final_weight'] = max(1, candidate['base_weight'] - penalty)

        # Weighted selection based on remaining tickets
        names = [c['name'] for c in pool]
        weights = [c['final_weight'] for c in pool]
        
        winner_name = random.choices(names, weights=weights, k=1)[0]
        
        # Move winner to selected_team
        idx = next(i for i, c in enumerate(pool) if c['name'] == winner_name)
        selected_team.append(pool.pop(idx))

    # 6. Output
    if selected_team:
        avg_exp = sum(p['exp'] for p in selected_team) / len(selected_team)
        print(f"\n✅ PROPOSED TEAM: {target_category}")
        print("-" * 50)
        for i, m in enumerate(selected_team):
            role = "LEAD" if i < reqs["lead"] else "SUPPORT"
            print(f"{role.ljust(10)} | {m['name'].ljust(15)} | Exp: {m['exp']}")
        
        print("-" * 50)
        print(f"📊 Team Avg Exp: {avg_exp:.2f}")
        if 1.5 <= avg_exp <= 2.5:
            print("✨ Status: Balanced")
        else:
            print("⚠️ Status: Unbalanced (High density of Veterans or Juniors)")
    else:
        print("❌ No eligible candidates found for this month.")

if __name__ == "__main__":
    get_optimized_team()