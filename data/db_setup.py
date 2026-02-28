import sqlite3
import os

def setup_database():

    if not os.path.exists('data'): #if it doesnt exist make a folder called data
        os.makedirs('data')
        

    conn = sqlite3.connect('data/aria_main.db')
    cursor = conn.cursor()

        # RA Table: RA information

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS RA (

            ra_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,
 
            role TEXT,
                   
            semester_joined TEXT CHECK(semester_joined IN ('S23', 'S24','F24', 'S25', 'F25', 'S26', 'F26')),
                   
            not_available TEXT,
            
            interests TEXT,   -- e.g., "Gaming, Cooking"

            skills TEXT      -- e.g., "Logistics, Design"
            
        )

    ''')



    # Programs Table: upcoming/past programming

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS programs (

            program_id INTEGER PRIMARY KEY AUTOINCREMENT,

            program_name TEXT NOT NULL,
            
            program_date DATETIME,
            
                  
            category TEXT,
            scale INTEGER, -- 1-4 (small, medium, large, huge)
            required_skills TEXT,
            
            semester_held TEXT CHECK(semester_held IN ('S23','F24', 'S25', 'F25', 'S26', 'W26','F26')),
            
            previous_iteration_id INTEGER, 
            FOREIGN KEY (previous_iteration_id) REFERENCES programs (program_id)

        )

    ''')



    # Assignments Table: for matching RAs to events (via AI)

    cursor.execute('''

        CREATE TABLE IF NOT EXISTS assignments (

            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            ra_id INTEGER,

            program_id INTEGER,
                   
            ra_role TEXT, -- lead or support ?
                   
            success_score FLOAT, -- How well the event went (1.0 - 10.0)

            FOREIGN KEY (ra_id) REFERENCES RA (ra_id),

            FOREIGN KEY (program_id) REFERENCES programs (program_id)

        )

    ''')



    conn.commit()

    conn.close()

    print("✅ Database initialized at data/aira_main.db")



if __name__ == "__main__":

    setup_database()