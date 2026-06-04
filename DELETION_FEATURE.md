# 🗑️ Data Deletion Feature Implementation

## Overview
Complete deletion functionality has been added to both frontend and backend for safely removing game, week, and season data from the Fantasy Football database.

---

## Frontend Changes (`ingest/frontend/index.html`)

### New Tab
- **Name**: "Data Deletion & Cleanup"
- **Icon**: `trash-2`
- **Location**: Added to tabs array before Stats & Fantasy

### Input Fields
1. **Game Deletion**
   - ESPN Event ID input field
   - Validates ESPN format (e.g., `xxxxxxxx-xxxx-xxxx-xxxx`)
   - Deletes the specific game and its related data

2. **Week Deletion**
   - Year input (1-2026)
   - Week input (1-18)
   - Deletes all data from the specified week

3. **Season Deletion**
   - Season Year input (1-2029)
   - Deletes all data from the entire season

### UI Features
- Red-themed delete buttons
- Visual indicators when inputs are filled
- Disabled state when operations are pending
- Success/error message display
- Confirmation modal with delete type information

### JavaScript Functions
```javascript
async deleteGame()      // Validates and sets up game deletion
async deleteWeek()      // Validates and sets up week deletion
async deleteSeason()    // Validates and sets up season deletion
async deleteData()      // Makes actual DELETE request to backend
function performDeletion() // Triggers the deleteData call
```

### Validation Rules
- **Game**: Valid ESPN event ID format required
- **Week**: Year 1-2026, Week 1-18
- **Season**: Year 1-2029

---

## Backend Changes (`ingest/service/app.py`)

### New Endpoints

#### 1. Delete Single Game
```python
@app.delete("/api/delete/game")
async def delete_game(event_id: str = Query(...)):
```

- Deletes the game and all related data in order:
  1. `game_dates` table
  2. `games` table
  3. `player_game_stats` table
  4. `team_game_stats` table

#### 2. Delete Week
```python
@app.delete("/api/delete/week")
async def delete_week(year: int, week: int):
```

- Deletes all data for a specific year-week:
  1. `game_dates` table (Wed-Tue for that week)
  2. `games` table
  3. `player_game_stats` tables
  4. `team_game_stats` tables

#### 3. Delete Season
```python
@app.delete("/api/delete/season")
async def delete_season(year: int):
```

- Deletes all data from the entire season:
  1. `games` table
  2. `player_game_stats` tables
  3. `team_game_stats` tables

### All operations:
- Use PostgreSQL transaction scope for atomic deletes
- Return success/error JSON responses
- Log deletion operations to server logs

---

## Usage

1. **Navigate to the Deletion tab** in the nflDash dashboard
2. **Choose deletion type** (Game/Week/Season)
3. **Enter parameters** (Year/Week/ESPON Event ID)
4. **Click delete button** to open confirmation dialog
5. **Confirm** to perform deletion
6. **View success message** - data is deleted from database

---

## Backend Endpoint Usage Examples

### Frontend calls the backend:
```javascript
// Game deletion
const deleteRes = await fetch('http://localhost:8002/api/delete/game?event_id=abcxyz-1234-5678-9012', {
  method: 'DELETE'
});
const result = await deleteRes.json();
```

### Backend handles the request:
```python
# FastAPI automatically captures the DELETE request
@app.delete("/api/delete/game", response_model=dict)
async def delete_game(event_id: str = Query(...)):
```

---

## Testing

### Test Game Deletion:
1. Go to Ingestion tab
2. Note the ESPN event ID of any game
3. Go to Deletion tab
4. Paste the ESPN event ID
5. Click "Delete Game"
6. Confirm deletion
7. Verify game is removed from Games tab

### Test Season Deletion:
1. Go to Deletion tab
2. Select Year 2022
3. Click "Delete Season"
4. Confirm deletion
5. Verify no 2022 data in database

---

## Important Notes

- **Destructive Operations**: Always confirm before deleting
- **Warning Messages**: Shows in frontend before deletion
- **Error Handling**: Frontend catches network errors and displays them
- **Backend Logs**: Uses PostgreSQL transaction for atomic commits
- **Console Logs**: Backend logs confirm successful deletions

---

## Files Modified

1. **Frontend**: `ingest/frontend/index.html`
   - Added deletion tab UI
   - Added form inputs for game/week/season
   - Added confirmation modal
   - Added fetch-based delete functions

2. **Backend**: `ingest/service/app.py`
   - Added `/api/delete/game` endpoint
   - Added `/api/delete/week` endpoint
   - Added `/api/delete/season` endpoint
