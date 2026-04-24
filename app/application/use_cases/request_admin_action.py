import uuid
from app.domain.models.approval_ticket import ApprovalTicket


class RequestAdminActionUseCase:
    async def execute(self, action_name:str,payload:dict) -> ApprovalTicket:
        """
        请求管理员操作
        """
        return ApprovalTicket(
            ticket_id=str(uuid.uuid4()),
            action_name=action_name,
            status="PENDING",
            payload=payload,
        )