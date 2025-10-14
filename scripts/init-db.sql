-- Expect psql to pass: -v app_user=<role_name>
-- We store it in a server-side GUC so PL/pgSQL can read it safely.
SELECT set_config('app.app_user', :'app_user', false);

-- Initialize database privileges for fba_user
-- This script ensures the application user has full access to the public schema
-- Run as superuser on database initialization
-- Expects app_user via psql -v; defaults to fba_user if not provided, but script provides it.

-- Create the application user if it doesn't exist
DO $do$
DECLARE
    v_app_user text := current_setting('app.app_user', true);
BEGIN
    IF v_app_user IS NULL THEN
        RAISE EXCEPTION 'app.app_user GUC not set';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_app_user) THEN
        EXECUTE format('CREATE ROLE %I LOGIN SUPERUSER', v_app_user);
    END IF;
END
$do$;

-- Grant connect privilege to the database
GRANT CONNECT ON DATABASE fba_bench TO :"app_user";

-- Grant schema privileges
GRANT USAGE, CREATE ON SCHEMA public TO :"app_user";

-- Grant privileges on existing objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO :"app_user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO :"app_user";
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO :"app_user";

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO :"app_user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO :"app_user";

-- Ensure the user owns the database (optional, for completeness)
ALTER DATABASE fba_bench OWNER TO :"app_user";