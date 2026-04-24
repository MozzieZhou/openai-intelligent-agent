
class ConfirmAdminActionUseCase:
    def __init__(self, approval_port, script_port):
        self.approval_port = approval_port
        self.script_port = script_port

    async def execute(self, ticket_id: str, approved: bool, operator: str) -> dict:
        """
        确认管理员操作
        """
        ticket = await self.approval_port.update(ticket_id, approved=approved, operator=operator)
        if ticket.status != "APPROVED":
            return {"status": ticket.status, "message": "已拒绝或待处理"}
        result = await self.script_port.execute(ticket.action_name, ticket.payload)
        return {"status": "EXECUTED", "result": result}
        
