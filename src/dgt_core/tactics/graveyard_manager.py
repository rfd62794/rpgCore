"""
Universal Registry Extensions - Graveyard and Permadeath Support
ADR 171: Graveyard Logic for Permadeath System
"""

import sqlite3
import json
import time
from typing import Optional, Dict, Any, List

from loguru import logger


class GraveyardManager:
    """Manages the graveyard for permadeath system"""
    
    def __init__(self, db_path: str = "roster.db"):
        self.db_path = db_path
        self._init_graveyard_table()
        
        logger.debug("⚰️ GraveyardManager initialized")
    
    def _init_graveyard_table(self):
        """Initialize graveyard table in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graveyard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ship_id TEXT UNIQUE NOT NULL,
                    death_time REAL NOT NULL,
                    death_cause TEXT NOT NULL,
                    final_generation INTEGER DEFAULT 0,
                    total_victories INTEGER DEFAULT 0,
                    total_xp INTEGER DEFAULT 0,
                    last_engine_type TEXT DEFAULT 'unknown',
                    epitaph TEXT,
                    genome_snapshot TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.commit()
        
        logger.info("⚰️ Graveyard table initialized")
    
    def move_to_graveyard(self, ship_id: str, death_cause: str, epitaph: str, 
                         final_stats: Optional[Dict[str, Any]] = None,
                         genome_snapshot: Optional[str] = None):
        """Move a ship to the graveyard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get final stats from fleet_roster if not provided
                if not final_stats:
                    cursor = conn.execute("""
                        SELECT generation, total_victories, total_xp, last_engine_type 
                        FROM fleet_roster WHERE ship_id = ?
                    """, (ship_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        final_stats = {
                            "generation": row[0],
                            "total_victories": row[1],
                            "total_xp": row[2],
                            "last_engine_type": row[3]
                        }
                    else:
                        final_stats = {
                            "generation": 0,
                            "total_victories": 0,
                            "total_xp": 0,
                            "last_engine_type": "unknown"
                        }
                
                # Insert into graveyard
                conn.execute("""
                    INSERT OR REPLACE INTO graveyard 
                    (ship_id, death_time, death_cause, final_generation, total_victories, 
                     total_xp, last_engine_type, epitaph, genome_snapshot)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ship_id,
                    time.time(),
                    death_cause,
                    final_stats.get("generation", 0),
                    final_stats.get("total_victories", 0),
                    final_stats.get("total_xp", 0),
                    final_stats.get("last_engine_type", "unknown"),
                    epitaph,
                    genome_snapshot
                ))
                
                # Remove from active fleet
                conn.execute("DELETE FROM fleet_roster WHERE ship_id = ?", (ship_id,))
                
                conn.commit()
            
            logger.info(f"⚰️ Moved {ship_id} to graveyard: {death_cause}")
            return True
            
        except Exception as e:
            logger.error(f"⚰️ Failed to move {ship_id} to graveyard: {e}")
            return False
    
    def get_graveyard_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get graveyard entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT ship_id, death_time, death_cause, final_generation, 
                           total_victories, total_xp, last_engine_type, epitaph
                    FROM graveyard 
                    ORDER BY death_time DESC 
                    LIMIT ?
                """, (limit,))
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        "ship_id": row[0],
                        "death_time": row[1],
                        "death_cause": row[2],
                        "final_generation": row[3],
                        "total_victories": row[4],
                        "total_xp": row[5],
                        "last_engine_type": row[6],
                        "epitaph": row[7]
                    })
                
                return entries
                
        except Exception as e:
            logger.error(f"⚰️ Failed to get graveyard entries: {e}")
            return []
    
    def get_graveyard_stats(self) -> Dict[str, Any]:
        """Get graveyard statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total deaths
                cursor = conn.execute("SELECT COUNT(*) FROM graveyard")
                total_deaths = cursor.fetchone()[0]
                
                # Deaths by cause
                cursor = conn.execute("""
                    SELECT death_cause, COUNT(*) 
                    FROM graveyard 
                    GROUP BY death_cause
                """)
                deaths_by_cause = dict(cursor.fetchall())
                
                # Average generation
                cursor = conn.execute("SELECT AVG(final_generation) FROM graveyard")
                avg_generation = cursor.fetchone()[0] or 0
                
                # Total victories lost
                cursor = conn.execute("SELECT SUM(total_victories) FROM graveyard")
                total_victories_lost = cursor.fetchone()[0] or 0
                
                # Recent deaths (last 24 hours)
                day_ago = time.time() - 86400
                cursor = conn.execute("SELECT COUNT(*) FROM graveyard WHERE death_time > ?", (day_ago,))
                recent_deaths = cursor.fetchone()[0]
                
                return {
                    "total_deaths": total_deaths,
                    "deaths_by_cause": deaths_by_cause,
                    "average_generation": round(avg_generation, 1),
                    "total_victories_lost": total_victories_lost,
                    "recent_deaths_24h": recent_deaths
                }
                
        except Exception as e:
            logger.error(f"⚰️ Failed to get graveyard stats: {e}")
            return {}
    
    def resurrect_ship(self, ship_id: str, cost: int) -> bool:
        """Resurrect a ship from graveyard (premium feature)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get graveyard entry
                cursor = conn.execute("""
                    SELECT genome_snapshot FROM graveyard WHERE ship_id = ?
                """, (ship_id,))
                row = cursor.fetchone()
                
                if not row:
                    logger.warning(f"⚰️ Ship {ship_id} not found in graveyard")
                    return False
                
                genome_snapshot = row[0]
                
                # Move back to fleet_roster
                if genome_snapshot:
                    # Parse genome snapshot and restore
                    genome_data = json.loads(genome_snapshot)
                    
                    conn.execute("""
                        INSERT INTO fleet_roster 
                        (ship_id, generation, total_xp, space_victories, shell_victories, 
                         last_engine_type, trait_snapshot)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ship_id,
                        genome_data.get("generation", 0),
                        genome_data.get("total_xp", 0),
                        genome_data.get("space_victories", 0),
                        genome_data.get("shell_victories", 0),
                        genome_data.get("last_engine_type", "space"),
                        genome_snapshot
                    ))
                else:
                    # Create basic entry
                    conn.execute("""
                        INSERT INTO fleet_roster 
                        (ship_id, generation, total_xp, space_victories, shell_victories, 
                         last_engine_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (ship_id, 1, 0, 0, 0, "space"))
                
                # Remove from graveyard
                conn.execute("DELETE FROM graveyard WHERE ship_id = ?", (ship_id,))
                
                conn.commit()
            
            logger.info(f"⚰️ Resurrected {ship_id} from graveyard (cost: {cost} credits)")
            return True
            
        except Exception as e:
            logger.error(f"⚰️ Failed to resurrect {ship_id}: {e}")
            return False
    
    def clear_graveyard(self) -> bool:
        """Clear all graveyard entries (admin function)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM graveyard")
                conn.commit()
            
            logger.warning("⚰️ Graveyard cleared")
            return True
            
        except Exception as e:
            logger.error(f"⚰️ Failed to clear graveyard: {e}")
            return False
