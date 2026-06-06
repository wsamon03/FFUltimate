### Game Score Schema Design

*   **Core Lesson**: Denormalize match results (home_score, away_score) into the games table rather than relying exclusively on fact tables (team_game_stats).
*   **Why**: Fetching the score from fact tables requires JOINs. Keeping it in the dimension table makes the primary display/API faster.
*   **Rule**: The games table must serve as the authoritative source for game metadata and final scores.
