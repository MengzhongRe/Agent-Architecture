# Datetime Tool工具,让LLM能够知道实时时间,日期.避免LLM活在训练数据的时间戳中

from agent import Tool
from datetime import datetime

class DateTimeTool(Tool):
    """Datetime工具类:返回当地时间"""
    def __init__(self):
        super().__init__(
            name='datetime',
            description=(
                "Get the current date, time, and day of week. "
                "Use when the user asks about today's date, current time, "
                "or what day it is. "
                "Returns: formatted datetime string like '2026-06-09, Monday, 15:30:45 CST'. "
                "Note: does NOT accept parameters. For tomorrow/yesterday/next week, "
                "call this tool first to get today, then calculate manually."
            ),
        )
    
    def execute(self, input_str: str | None = None) -> str:
        now = datetime.now()
        return now.strftime('%Y-%m-%d %A %H:%M:%S') + ' (local time)'

if __name__ == '__main__':
    datetime_tool = DateTimeTool()
    now_time = datetime_tool.execute()
    print(now_time)