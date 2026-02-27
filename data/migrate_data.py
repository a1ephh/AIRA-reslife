import sqlite3
import pandas as pd


def link_iterations(cursor):
    """Links programs with the same name across different semesters."""
    # Find all program names that appear more than once
    cursor.execute('''
        SELECT program_name FROM programs 
        GROUP BY program_name HAVING COUNT(*) > 1
    ''')
    repeated_programs = [row[0] for row in cursor.fetchall()]

    for name in repeated_programs:
        # Get all versions of this program ordered by date
        cursor.execute('''
            SELECT program_id FROM programs 
            WHERE program_name = ? 
            ORDER BY program_date ASC
        ''', (name,))
        
        ids = [row[0] for row in cursor.fetchall()]
        
        # Link them: ID 2 points to ID 1, ID 3 points to ID 2, etc.
        for i in range(1, len(ids)):
            current_id = ids[i]
            previous_id = ids[i-1]
            cursor.execute('''
                UPDATE programs 
                SET previous_iteration_id = ? 
                WHERE program_id = ?
            ''', (previous_id, current_id))
    
    print(f"🔗 Linked {len(repeated_programs)} recurring program series.")

def migrate_data():
    db_path = 'data/aria_main.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- PART 1: RA ROSTER ---
    try:
        df_ra_roster = pd.read_csv('RA_data.csv') 
        for _, row in df_ra_roster.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO RA (name, role, semester_joined)
                VALUES (?, ?, ?)
            ''', (row['Name'], row['Role'], row['Starting Semester']))
        print(f"✅ RA Roster imported.")
    except Exception as e:
        print(f"❌ Error loading RA_data.csv: {e}")

    # --- PART 2: PROGRAMS & ASSIGNMENTS ---
    try:
        df_programs = pd.read_csv('past_programs.csv')
        df_programs = df_programs.dropna(subset=['Program']) #to ignore null values in the Program column

        df_programs['Date'] = pd.to_datetime(df_programs['Date']).dt.strftime('%Y-%m-%d')
        scale_map = {'small': 1, 'medium': 2, 'large': 3, 'extra large': 4}

        for _, row in df_programs.iterrows():
            # CHANGE: Look up by Name, Semester, AND Date
            cursor.execute('''
            SELECT program_id FROM programs 
            WHERE program_name = ? AND semester_held = ? AND program_date = ?
            ''', (row['Program'], row['Semester'], row['Date']))

            prog_result = cursor.fetchone()

            if not prog_result:
                # Create a UNIQUE entry for this specific date
                scale_val = scale_map.get(str(row['Scale']).lower(), 1)
                cursor.execute('''
                    INSERT INTO programs (program_name, program_date, category, scale, semester_held) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['Program'], row['Date'], row['Program Tag'], scale_val, row['Semester']))
                program_id = cursor.lastrowid
            else:
                program_id = prog_result[0]

            # Find RA ID
            cursor.execute("SELECT ra_id FROM RA WHERE name = ?", (row['RA'],))
            ra_result = cursor.fetchone()
            
            if ra_result:
                ra_id = ra_result[0]
                # Create the Assignment
                cursor.execute('''
                    INSERT INTO assignments (ra_id, program_id, ra_role, success_score)
                    VALUES (?, ?, ?, ?)
                ''', (ra_id, program_id, row['Role'], None))  # Success Score can be calculated later

        print("✅ Multi-semester Programs and Assignments migration complete.")

    except Exception as e:
        print(f"❌ Error loading past_programs.csv: {e}")

    link_iterations(cursor)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_data()