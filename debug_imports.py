
try:
    from langchain.agents import create_react_agent
    print("✅ langchain.agents.create_react_agent ok")
except ImportError as e:
    print(f"❌ langchain.agents.create_react_agent failed: {e}")

try:
    from langchain.agents import AgentExecutor
    print("✅ langchain.agents.AgentExecutor ok")
except ImportError as e:
    print(f"❌ langchain.agents.AgentExecutor failed: {e}")

try:
    from langchain_core.agents import AgentExecutor
    print("✅ langchain_core.agents.AgentExecutor ok")
except ImportError as e:
    print(f"❌ langchain_core.agents.AgentExecutor failed: {e}")

try:
    from langchain.tools import Tool
    print("✅ langchain.tools.Tool ok")
except ImportError as e:
    print(f"❌ langchain.tools.Tool failed: {e}")

try:
    from langchain_core.tools import Tool
    print("✅ langchain_core.tools.Tool ok")
except ImportError as e:
    print(f"❌ langchain_core.tools.Tool failed: {e}")
