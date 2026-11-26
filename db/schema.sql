-- Customers table.
-- Run by the tests (CI) and by every deploy job before the new code goes live.
-- IF NOT EXISTS makes it safe to run again: an existing table is left as it is.
-- Note: it only creates the table. Changing an existing column later would need
-- a migration step, which this project does not have yet.
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- assigned by the database
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,                              -- no duplicates; the API returns 409
    phone      TEXT,                                              -- optional
    active     BOOLEAN NOT NULL DEFAULT TRUE,                     -- FALSE = soft deleted
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()                 -- set by the API on every update
);
