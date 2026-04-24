from typing import Literal
from pydantic import BaseModel

TicketStatus = Literal["PENDING", "APPROVED", "REJECTED", "EXECUTED", "FAILED"]

class ApprovalTicket(BaseModel):
    ticket_id: str
    action_name: str
    status: TicketStatus
    payload: dict = {}
