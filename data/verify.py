import sqlite3

def run_audit():
    conn = sqlite3.connect('data/aria_main.db')
    cursor = conn.cursor()

    print("\n--- 🏆 RA Experience Leaderboard ---")
    # This query joins RA to Assignments to count their history
    cursor.execute('''
        SELECT RA.name, COUNT(assignments.assignment_id) as total_programs
        FROM RA
        LEFT JOIN assignments ON RA.ra_id = assignments.ra_id
        GROUP BY RA.name
        ORDER BY total_programs DESC
        LIMIT 5
    ''')
    
    for name, count in cursor.fetchall():
        print(f"RA: {name.ljust(15)} | Programs Completed: {count}")

    print("\n--- 🔗 Recurring Program Links ---")
    # This checks if our iteration linking worked
    cursor.execute('''
        SELECT p1.program_name, p1.semester_held, p2.semester_held as previous_held
        FROM programs p1
        JOIN programs p2 ON p1.previous_iteration_id = p2.program_id
        LIMIT 20
    ''')
    
    links = cursor.fetchall()
    if not links:
        print("No linked iterations found yet. (Or no programs have repeats!)")
    for name, current, prev in links:
        print(f"Program: {name.ljust(20)} | Current: {current} | Linked to: {prev}")

    conn.close()

if __name__ == "__main__":
    run_audit()