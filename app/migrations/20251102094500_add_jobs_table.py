"""
This module contains a Caribou migration.

Migration Name: add_jobs_table
Migration Version: 20251102094500
"""


def upgrade(connection):
    sql = """
    CREATE TABLE "jobs" (
        "id" TEXT PRIMARY KEY UNIQUE NOT NULL,
        "url" TEXT NOT NULL,
        "status" TEXT NOT NULL,
        "filepath" TEXT,
        "error" TEXT,
        "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    connection.execute(sql)
    connection.commit()


def downgrade(connection):
    sql = """
    DROP TABLE IF EXISTS "jobs";
    """
    connection.execute(sql)
    connection.commit()
