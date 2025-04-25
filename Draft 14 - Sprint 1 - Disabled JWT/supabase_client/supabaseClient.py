from supabase import create_client, Client

SUPABASE_URL = "https://nlnqftrcipwrjeikexdp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sbnFmdHJjaXB3cmplaWtleGRwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTExMjI1MywiZXhwIjoyMDYwNjg4MjUzfQ.0H5DnKEAkOJJABR1BZOC9LteZS8vhtMNLq9vYHnlfjY"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def supabase_create_client(jwt_token: str) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Set JWT token for PostgREST (database) requests
    client.postgrest.auth(jwt_token)
    return client