import sqlite3

DATABASE = "blog.db"

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

cursor.execute("PRAGMA table_info(posts)")

columns = [
    row[1]
    for row in cursor.fetchall()
]

print("Existing posts columns:")
print(columns)

if "status" not in columns:
    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN status VARCHAR(20)
        NOT NULL
        DEFAULT 'published'
    """)
    print("Added: status")
else:
    print("status already exists")

if "scheduled_at" not in columns:
    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN scheduled_at DATETIME
    """)
    print("Added: scheduled_at")
else:
    print("scheduled_at already exists")

if "published_at" not in columns:
    cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN published_at DATETIME
    """)
    print("Added: published_at")
else:
    print("published_at already exists")

connection.commit()

cursor.execute("PRAGMA table_info(posts)")

print("")
print("Updated posts columns:")

for row in cursor.fetchall():
    print(
        row[1],
        "|",
        row[2],
        "| default:",
        row[4]
    )

connection.close()

print("")
print("Database migration completed successfully.")
