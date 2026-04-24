
from pydantic import BaseModel

"""
用户会话上下文模型
"""
class ConversationContext(BaseModel):
    user_id: str
    session_id: str
    trace_id: str
    channel: str = "web"
