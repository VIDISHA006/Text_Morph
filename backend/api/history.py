#!/usr/bin/env python3
"""
History Management Routes
Handles user's processing history for summaries and paraphrases
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import mysql.connector
from .database import get_db_connection
from .dependencies import get_current_user

router = APIRouter(prefix="/history", tags=["history"])

# Models
class HistoryCreate(BaseModel):
    user_id: int
    original_text: str
    processed_text: str
    processing_type: str  # 'summary' or 'paraphrase'
    model_used: Optional[str] = ""

class HistoryUpdate(BaseModel):
    processed_text: str

class HistoryResponse(BaseModel):
    id: int
    user_id: int
    original_text: str
    processed_text: str
    processing_type: str
    model_used: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_history(history_data: HistoryCreate, current_user: dict = Depends(get_current_user)):
    """Save a new history item"""
    
    # Verify user can only save to their own history
    if current_user["id"] != history_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot save to another user's history"
        )
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        cursor = connection.cursor()
        
        # Create history table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                original_text TEXT NOT NULL,
                processed_text TEXT NOT NULL,
                processing_type VARCHAR(50) NOT NULL,
                model_used VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_created (user_id, created_at DESC)
            )
        """)
        
        # Insert history item
        cursor.execute("""
            INSERT INTO processing_history 
            (user_id, original_text, processed_text, processing_type, model_used)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            history_data.user_id,
            history_data.original_text,
            history_data.processed_text,
            history_data.processing_type,
            history_data.model_used
        ))
        
        connection.commit()
        return {"message": "History saved successfully", "id": cursor.lastrowid}
        
    except mysql.connector.Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        connection.close()

@router.get("/user/{user_id}", response_model=List[HistoryResponse])
async def get_user_history(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get processing history for a user"""
    
    # Verify user can only access their own history
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's history"
        )
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user's history ordered by creation date (newest first)
        cursor.execute("""
            SELECT id, user_id, original_text, processed_text, processing_type, 
                   model_used, created_at, updated_at
            FROM processing_history 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 100
        """, (user_id,))
        
        history_items = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings
        for item in history_items:
            if item['created_at']:
                item['created_at'] = item['created_at'].isoformat()
            if item['updated_at']:
                item['updated_at'] = item['updated_at'].isoformat()
        
        return history_items
        
    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        connection.close()

@router.put("/update/{item_id}")
async def update_history_item(item_id: int, update_data: HistoryUpdate, current_user: dict = Depends(get_current_user)):
    """Update a history item's processed text"""
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        cursor = connection.cursor()
        
        # Verify the item belongs to the current user
        cursor.execute("""
            SELECT user_id FROM processing_history WHERE id = %s
        """, (item_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found"
            )
        
        if result[0] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update another user's history item"
            )
        
        # Update the processed text
        cursor.execute("""
            UPDATE processing_history 
            SET processed_text = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (update_data.processed_text, item_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found"
            )
        
        connection.commit()
        return {"message": "History item updated successfully"}
        
    except mysql.connector.Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        connection.close()

@router.delete("/delete/{item_id}")
async def delete_history_item(item_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a history item"""
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        cursor = connection.cursor()
        
        # Verify the item belongs to the current user
        cursor.execute("""
            SELECT user_id FROM processing_history WHERE id = %s
        """, (item_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found"
            )
        
        if result[0] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete another user's history item"
            )
        
        # Delete the item
        cursor.execute("""
            DELETE FROM processing_history WHERE id = %s
        """, (item_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found"
            )
        
        connection.commit()
        return {"message": "History item deleted successfully"}
        
    except mysql.connector.Error as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        connection.close()

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get user's processing statistics"""
    
    # Verify user can only access their own stats
    if current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's statistics"
        )
    
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    
    try:
        cursor = connection.cursor()
        
        # Get statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN processing_type = 'summary' THEN 1 ELSE 0 END) as summaries,
                SUM(CASE WHEN processing_type = 'paraphrase' THEN 1 ELSE 0 END) as paraphrases,
                MIN(created_at) as first_item,
                MAX(created_at) as last_item
            FROM processing_history 
            WHERE user_id = %s
        """, (user_id,))
        
        stats = cursor.fetchone()
        
        return {
            "total_items": stats[0] or 0,
            "summaries": stats[1] or 0,
            "paraphrases": stats[2] or 0,
            "first_item": stats[3].isoformat() if stats[3] else None,
            "last_item": stats[4].isoformat() if stats[4] else None
        }
        
    except mysql.connector.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        connection.close()