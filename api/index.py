import os
import sys

# Add parent directory to path so server module can be imported
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import server

# Ensure database is initialized in /tmp on Vercel
try:
    server.init_db()
except Exception as e:
    print("Vercel DB Init error:", e)

# Export handler class for Vercel Serverless Python runtime
class handler(server.EcommerceRequestHandler):
    def __init__(self, *args, **kwargs):
        # When running in serverless, directory is parent_dir
        super(server.EcommerceRequestHandler, self).__init__(*args, directory=parent_dir, **kwargs)
