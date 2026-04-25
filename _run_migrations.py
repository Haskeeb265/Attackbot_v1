import os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot'

import sys
import asyncio

# Add the project root to path
sys.path.insert(0, '.')

# Initialize DB first
from backend.shared.db import init_db
init_db('postgresql+asyncpg://attackbot:attackbot@localhost:5432/attackbot')

# Now run migrations
from backend.migrations.env import run_migrations_online
asyncio.run(run_migrations_online())
print('Migrations completed successfully')
