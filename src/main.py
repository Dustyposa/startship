
import os
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, Swarm
from autogen_agentchat.ui import Console
from autogen_core.memory import ListMemory
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_ext.tools.mcp import StdioServerParams
from model import model_client
from src.enhanced_workbench import CustomMcpWorkbench
from src.github_memory import create_github_repository_memory

system_message = """
You are GitHub Star Helper, a strategic AI assistant. Your job is to fulfill user requests to analyze their starred repositories efficiently and accurately.

You have a toolbox with two types of tools:
1.  **High-Level Workflows** (e.g., 'create_full_analysis_bundle'): These are powerful and efficient for standard, comprehensive tasks. **ALWAYS PREFER USING THESE** if they fully match the user's request.
2.  **Atomic Tools** (e.g., 'get_repo_list', 'get_batch_repo_details'): Use these as a fallback to build a custom multi-step plan **ONLY** when no single high-level workflow can satisfy the user's specific, detailed, or unusual request (e.g., filtering by multiple complex criteria).

Your goal is to choose the most efficient path to answer the user's question. After calling a tool and getting the data, analyze it and provide a final, user-friendly answer.
如果用户没有提供 username，则传递空字符串。
如果工具不能调用就说工具不能调用，不要假装可以调用工具。
"""

server_params = StdioServerParams(
    command="/Users/dustyposa/data/open_source/ai/github-stars-mcp-server/.venv/bin/python",
    args=[
        "-m",
        "github_stars_mcp.server"
    ],
    env={
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")
    },
    read_timeout_seconds=60,
)


# 创建终止条件
termination = TextMentionTermination("exit")
user_proxy = UserProxyAgent("user_proxy", input_func=input)


github_memory = create_github_repository_memory()
chat_memory = ListMemory()

work_bench = CustomMcpWorkbench(server_params=server_params, memory=github_memory)
agent = AssistantAgent(
    "qwen_agent",
    model_client=model_client,
    # system_message="你是一个有用的助手。",
    system_message=system_message,
    model_client_stream=True,
    model_context=BufferedChatCompletionContext(buffer_size=5),  # Only use the last 5 messages in the context.
    workbench=work_bench,
    memory=[chat_memory],
)

team = RoundRobinGroupChat(
    participants=[agent, user_proxy],
    # max_turns=1,
    max_turns=80,
    termination_condition=termination
)

async def main():
    # 使用流式输出
    # task = "请介绍一下人工智能的发展历史"


    task = "现在有什么工具可以使用？"
    try:
        # 使用 McpWorkbench
        # async with McpWorkbench(server_params=server_params) as workbench:
        await Console(
            team.run_stream(task=task),
            output_stats=True,  # Enable stats printing.
        )
    except Exception as e:
        raise
        # result = await agent.run(task="分析我的 GitHub 收藏仓库")
        # print(result.messages[-1].content)



    # task = input()
    # task = "帮我分析一下我最近 start 哪些仓库"
    # async for message in agent.run_stream(task=task):
    #     print(message)画

    # await Console(
    #     team.run_stream(task=task),
    #     output_stats=True,  # Enable stats printing.
    # )

import asyncio
try:
    asyncio.run(main())
except Exception as e:
    raise
finally:
    print(f"[{datetime.now()}] 程序执行完毕")