-- Seed player_position lookup table
-- Run after schema is created but before inserting any data

CREATE OR REPLACE PROCEDURE usp_seed_player_position()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO player_position (position_code, description) VALUES
        ('QB', 'Quarterback'),
        ('RB', 'Running Back'),
        ('WR', 'Wide Receiver'),
        ('TE', 'Tight End'),
        ('K',  'Kicker'),
        ('DL', 'Defensive Lineman'),
        ('LB', 'Linebacker'),
        ('CB', 'Cornerback'),
        ('S',  'Safety'),
        ('DP', 'Defensive Player'),
        ('P',  'Punter'),
        ('HS', 'Defensive Specialist'),
        ('',   'Non-position / Special'),
        ('C',  'Center'),
        ('DE', 'Defensive End'),
        ('DT', 'Defensive Tackle'),
        ('FB', 'Fullback'),
        ('G',  'Guard'),
        ('LS', 'Long Snapper'),
        ('OT', 'Offensive Tackle'),
        ('PK', 'Placekicker')
    ON CONFLICT (position_code) DO NOTHING;
END;
$$;

SELECT 'Player position seed data inserted' AS status;
