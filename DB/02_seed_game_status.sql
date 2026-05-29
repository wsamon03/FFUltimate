-- Seed game_status lookup table
-- Run after schema is created but before inserting any data

CREATE OR REPLACE PROCEDURE usp_seed_game_status()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO game_status (status_code, description) VALUES
        ('scheduled', 'Game has not started'),
        ('live',     'Game is in progress'),
        ('final',    'Game is complete')
    ON CONFLICT (status_code) DO NOTHING;
END;
$$;

SELECT 'Game status seed data inserted' AS status;
