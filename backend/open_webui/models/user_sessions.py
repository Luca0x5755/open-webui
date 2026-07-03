"""[PATCH-A] 單一有效登入：使用者「當前有效 Session」的伺服器端記錄。

每位使用者一列，記錄其當前有效 token 的 `jti`。
新登入寫入新的 `jti`，舊 token 因 `jti` 不符而失效（見 utils/single_session.py）。
"""

import logging
import time
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, Text, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

####################
# DB MODEL
####################


class UserSession(Base):
    __tablename__ = 'user_session'

    # 一使用者一列；token 的 jti 即當前有效 Session 的識別碼
    user_id = Column(Text, ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    session_id = Column(Text, nullable=False)  # 當前有效 token 的 jti
    updated_at = Column(BigInteger, nullable=False)


class UserSessionModel(BaseModel):
    user_id: str
    session_id: str
    updated_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Table
####################


class UserSessionsTable:
    async def set_current_session(
        self, user_id: str, session_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[UserSessionModel]:
        """將 user_id 的當前有效 Session 覆寫為 session_id（存在則更新，否則新增）。"""
        try:
            async with get_async_db_context(db) as db:
                current_time = int(time.time())

                result = await db.execute(
                    update(UserSession)
                    .filter_by(user_id=user_id)
                    .values(session_id=session_id, updated_at=current_time)
                )
                if result.rowcount == 0:
                    db.add(
                        UserSession(
                            user_id=user_id,
                            session_id=session_id,
                            updated_at=current_time,
                        )
                    )
                await db.commit()

                return UserSessionModel(
                    user_id=user_id,
                    session_id=session_id,
                    updated_at=current_time,
                )
        except Exception as e:
            log.error(f'Error setting current session for user {user_id}: {e}')
            return None

    async def get_current_session_id(self, user_id: str, db: Optional[AsyncSession] = None) -> Optional[str]:
        """取得 user_id 的當前有效 Session 的 jti；無記錄回 None。"""
        try:
            async with get_async_db_context(db) as db:
                result = await db.execute(select(UserSession.session_id).filter_by(user_id=user_id))
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            log.error(f'Error getting current session for user {user_id}: {e}')
            return None

    async def clear(self, user_id: str, db: Optional[AsyncSession] = None) -> bool:
        """清除 user_id 的當前 Session 記錄（供登出使用，選用）。"""
        try:
            async with get_async_db_context(db) as db:
                await db.execute(delete(UserSession).filter_by(user_id=user_id))
                await db.commit()
                return True
        except Exception as e:
            log.error(f'Error clearing current session for user {user_id}: {e}')
            return False


UserSessions = UserSessionsTable()
