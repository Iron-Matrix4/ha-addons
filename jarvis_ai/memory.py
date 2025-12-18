import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Memory:
    """
    Persistent memory system for Jarvis.
    
    CRITICAL RULES:
    1. NEVER store HA entity states (always query live from HA)
    2. ONLY store user preferences and learned context
    3. Auto-prune conversation history older than 7 days
    4. Facts are for knowledge, NOT real-time data
    """
    
    def __init__(self, db_path: str = "/data/jarvis_memory.db"):
        """Initialize memory database."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        logger.debug(f"Memory system initialized at {db_path}")
    
    def _init_db(self):
        """Create database schema if not exists."""
        cursor = self.conn.cursor()
        
        # User Preferences (Static settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Learned Facts (Contextual knowledge, NOT states)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                entity_id TEXT,
                fact_key TEXT,
                fact_value TEXT,
                source TEXT,
                learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_id, fact_key)
            )
        """)
        
        # Conversation Context (Auto-pruned after 7 days)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT,
                assistant_response TEXT,
                is_error INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing context table to add is_error column if not exists
        try:
            cursor.execute("ALTER TABLE context ADD COLUMN is_error INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Last Interactions (For follow-up commands like "turn it off")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS last_interaction (
                context_type TEXT PRIMARY KEY,
                entity_id TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.debug("Memory database schema initialized")
    
    # ===== PREFERENCES =====
    
    def set_preference(self, key: str, value: Any):
        """
        Store a user preference.
        Examples: temperature_unit, skip_unit_suffix, favorite_color
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, json.dumps(value)))
        self.conn.commit()
        logger.debug(f"Preference set: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve a user preference."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return default
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences as a dictionary."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM preferences")
        prefs = {}
        for row in cursor.fetchall():
            prefs[row[0]] = json.loads(row[1])
        return prefs
    
    def delete_preference(self, key: str):
        """Delete a user preference."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM preferences WHERE key = ?", (key,))
        self.conn.commit()
        logger.debug(f"Preference deleted: {key}")
    
    # ===== FACTS =====
    
    def remember_fact(self, entity_id: str, fact_key: str, fact_value: str, source: str = "user"):
        """
        Store a learned fact about an entity.
        Examples: ("fish_tank", "ideal_temp_range", "24-26", "web_search")
        
        WARNING: Do NOT store current states! Only contextual knowledge.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO facts (entity_id, fact_key, fact_value, source, learned_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (entity_id, fact_key, fact_value, source))
        self.conn.commit()
        logger.debug(f"Fact remembered: {entity_id}.{fact_key} = {fact_value} (source: {source})")
    
    def recall_fact(self, entity_id: str, fact_key: str) -> Optional[str]:
        """Retrieve a learned fact about an entity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT fact_value FROM facts 
            WHERE entity_id = ? AND fact_key = ?
        """, (entity_id, fact_key))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_entity_facts(self, entity_id: str) -> Dict[str, str]:
        """Get all facts about a specific entity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT fact_key, fact_value FROM facts WHERE entity_id = ?
        """, (entity_id,))
        facts = {}
        for row in cursor.fetchall():
            facts[row[0]] = row[1]
        return facts
    
    def delete_fact(self, entity_id: str, fact_key: str):
        """Delete a specific fact."""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM facts WHERE entity_id = ? AND fact_key = ?
        """, (entity_id, fact_key))
        self.conn.commit()
        logger.debug(f"Fact deleted: {entity_id}.{fact_key}")
    
    # ===== CONVERSATION CONTEXT =====
    
    def save_context(self, user_input: str, assistant_response: str, is_error: bool = False):
        """Save a conversation exchange for context.
        
        Args:
            user_input: User's input text
            assistant_response: Jarvis's response
            is_error: Whether this was an error response (to filter out later)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO context (user_input, assistant_response, is_error, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_input, assistant_response, 1 if is_error else 0))
        self.conn.commit()
        
        # Auto-prune old context
        self._prune_old_context()
    
    def get_recent_context(self, limit: int = 5, include_errors: bool = False) -> list:
        """Get recent conversation exchanges, filtering out errors by default.
        
        Args:
            limit: Maximum number of context entries to return
            include_errors: If True, include error responses; if False, filter them out
        """
        cursor = self.conn.cursor()
        
        if include_errors:
            query = """
                SELECT user_input, assistant_response, timestamp
                FROM context
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
        else:
            # Exclude errors - only get successful interactions
            query = """
                SELECT user_input, assistant_response, timestamp
                FROM context
                WHERE is_error = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
        
        context = []
        for row in cursor.fetchall():
            context.append({
                'user': row[0],
                'assistant': row[1],
                'timestamp': row[2]
            })
        return list(reversed(context))  # Return in chronological order
    
    def _prune_old_context(self):
        """Delete conversation context older than 7 days."""
        cursor = self.conn.cursor()
        cutoff = datetime.now() - timedelta(days=7)
        cursor.execute("""
            DELETE FROM context WHERE timestamp < ?
        """, (cutoff,))
        deleted = cursor.rowcount
        self.conn.commit()
        if deleted > 0:
            logger.info(f"Pruned {deleted} old context entries")
    
    # ===== LAST INTERACTION =====
    
    def save_last_interaction(self, context_type: str, entity_id: str, action: str):
        """
        Save the last entity interaction for follow-up commands.
        context_type: 'light', 'climate', 'media', etc.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO last_interaction (context_type, entity_id, action, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (context_type, entity_id, action))
        self.conn.commit()
        logger.debug(f"Last interaction saved: {context_type} -> {entity_id} ({action})")
    
    def get_last_interaction(self, context_type: str) -> Optional[Dict[str, str]]:
        """Get the last interaction for a given context type."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT entity_id, action, timestamp FROM last_interaction
            WHERE context_type = ?
        """, (context_type,))
        row = cursor.fetchone()
        if row:
            return {
                'entity_id': row[0],
                'action': row[1],
                'timestamp': row[2]
            }
        return None
    
    # ===== UTILITY =====
    
    def clear_all_memory(self):
        """Clear all memory (use with caution!)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM preferences")
        cursor.execute("DELETE FROM facts")
        cursor.execute("DELETE FROM context")
        cursor.execute("DELETE FROM last_interaction")
        self.conn.commit()
        logger.warning("All memory cleared!")
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM preferences")
        stats['preferences'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM facts")
        stats['facts'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM context")
        stats['context_entries'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM last_interaction")
        stats['last_interactions'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.debug("Memory database closed")
