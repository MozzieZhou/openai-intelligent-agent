import re

class SqlPolicy:
    def __init__(self, allwod_tables:set[str]):
        self.allwod_tables = {t.lower() for t in allwod_tables}
    
    def validate(self,sql:str) -> tuple[bool,str]:
        """
        验证SQL语句是否符合策略
        1. 只能select        
        """
        s = sql.strip().lower()
        if ";" in s[:-1]:
            return False, "SQL语句中包含分号，仅允许单条语句"
        if not(s.startswith("select") or s.startswith("explain")):
           return False, "只允许 SELECT/EXPLAIN 查询"
        if any(k in s for k in [" insert ", " update ", " delete ", " drop ", " alter "]):
            return False, "只允许 SELECT/EXPLAIN 查询，不允许 INSERT/UPDATE/DELETE/DROP/ALTER 操作"
        
        tables = re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", s)
        if any(t not in self.allwod_tables for t in tables):
            return False, f"存在未授权表: {tables - self.allowed_tables}"
        return True, ""
