---
name: db-mgmt
description: SQLite and data migration guidance.
---

# Database Management Skill
This skill ensures data integrity and efficient handling of project databases.

## Instructions
- Use `safe_migrate.py` or similar robust patterns for updating database schemas.
- Always backup data before performing destructive operations.
- Ensure SQL queries are optimized and use parameterized inputs to prevent injection.
- Monitor database size and performance, especially when handling large sets of vocabulary or user data.
- Maintain clear mapping between application models and database tables.
