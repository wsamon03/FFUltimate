-- Themes table + user theme preference
-- Run after 03_user_api_schema.sql

CREATE TABLE IF NOT EXISTS user_api.themes (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50)  NOT NULL UNIQUE,
    display_name    VARCHAR(100) NOT NULL,
    primary_color   VARCHAR(20)  NOT NULL,
    primary_hover   VARCHAR(20)  NOT NULL,
    bg_color        VARCHAR(20)  NOT NULL,
    card_color      VARCHAR(20)  NOT NULL,
    card_hover      VARCHAR(20)  NOT NULL,
    border_color    VARCHAR(20)  NOT NULL,
    text_primary    VARCHAR(20)  NOT NULL,
    text_secondary  VARCHAR(20)  NOT NULL,
    font_family     TEXT         NOT NULL DEFAULT 'Inter, sans-serif',
    is_default      BOOLEAN      NOT NULL DEFAULT FALSE
);

INSERT INTO user_api.themes
    (name, display_name, primary_color, primary_hover, bg_color, card_color, card_hover, border_color, text_primary, text_secondary, font_family, is_default)
VALUES
    ('dark',   'Dark',   '#3b82f6', '#2563eb', '#0f172a', '#1e293b', '#263347', '#334155', '#f1f5f9', '#94a3b8', 'Inter, sans-serif', TRUE),
    ('light',  'Light',  '#2563eb', '#1d4ed8', '#f8fafc', '#ffffff', '#f1f5f9', '#e2e8f0', '#0f172a', '#64748b', 'Inter, sans-serif', FALSE),
    ('forest', 'Forest', '#10b981', '#059669', '#0d1f1a', '#1a2e26', '#223d32', '#2d5044', '#ecfdf5', '#6ee7b7', 'Inter, sans-serif', FALSE)
ON CONFLICT (name) DO NOTHING;

ALTER TABLE user_api.users
    ADD COLUMN IF NOT EXISTS active_theme_id INT REFERENCES user_api.themes(id);
