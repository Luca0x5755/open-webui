"""[PATCH-A] 單一有效登入（最後登入優先）。

同一帳號只保留最後一次登入的 Session；新登入會使前次登入的 token 立即失效。
不依賴 Redis，跨重啟仍有效。可用環境變數 ENABLE_SINGLE_ACTIVE_SESSION 關閉。
"""

import logging
import os

from open_webui.models.user_sessions import UserSessions
from open_webui.utils.auth import decode_token

log = logging.getLogger(__name__)

# 功能開關：預設開啟；設為 false 時回歸「同帳號可多處登入」的原行為。
ENABLE_SINGLE_ACTIVE_SESSION = os.getenv('ENABLE_SINGLE_ACTIVE_SESSION', 'True').lower() == 'true'


async def register_login_session(user_id: str, token: str) -> None:
    """登入時呼叫：將本次 token 設為該使用者唯一有效 Session，並踢掉前次登入。"""
    if not ENABLE_SINGLE_ACTIVE_SESSION:
        return

    decoded = decode_token(token)
    jti = decoded.get('jti') if decoded else None
    if not jti:
        return

    await UserSessions.set_current_session(user_id, jti)

    # 立即中斷前次登入裝置的 WebSocket 連線（延遲 import 避免循環相依）。
    try:
        from open_webui.socket.main import disconnect_user_sessions

        await disconnect_user_sessions(user_id)
    except Exception as e:
        log.debug(f'Skip disconnecting previous websocket sessions for {user_id}: {e}')


async def is_active_session(decoded: dict) -> bool:
    """驗證時呼叫：token 是否為該使用者當前有效的 Session。

    無記錄一律放行（平順上線，避免既有登入者被誤鎖）；
    有記錄且 jti 相符才有效，否則視為已被新登入踢掉。
    """
    if not ENABLE_SINGLE_ACTIVE_SESSION:
        return True

    user_id = decoded.get('id')
    jti = decoded.get('jti')
    if not user_id or not jti:
        return True

    current_jti = await UserSessions.get_current_session_id(user_id)
    if current_jti is None:
        return True

    return current_jti == jti
