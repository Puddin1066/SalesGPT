import re
from typing import Union

# Import AgentOutputParser with fallbacks for different langchain versions
try:
    from langchain.agents.agent import AgentOutputParser
except ImportError:
    try:
        from langchain_classic.agents.agent import AgentOutputParser
    except ImportError:
        try:
            from langchain_core.agents import AgentOutputParser
        except ImportError:
            # Create a placeholder if not available
            AgentOutputParser = None
            import warnings
            warnings.warn("AgentOutputParser not available - some features may be limited")
# Import FORMAT_INSTRUCTIONS with fallbacks
try:
    from langchain.agents.conversational.prompt import FORMAT_INSTRUCTIONS
except ImportError:
    try:
        from langchain_classic.agents.conversational.prompt import FORMAT_INSTRUCTIONS
    except ImportError:
        # Provide a default format instructions string
        FORMAT_INSTRUCTIONS = "Use the following format:\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of []\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question"
        import warnings
        warnings.warn("FORMAT_INSTRUCTIONS not available - using default")

# Import AgentAction, AgentFinish with fallbacks
try:
    from langchain.schema import AgentAction, AgentFinish
except ImportError:
    try:
        from langchain_core.agents import AgentAction, AgentFinish
    except ImportError:
        try:
            from langchain.schema.agent import AgentAction, AgentFinish
        except ImportError:
            # Create placeholders if not available
            AgentAction = None
            AgentFinish = None
            import warnings
            warnings.warn("AgentAction/AgentFinish not available - some features may be limited")


class SalesConvoOutputParser(AgentOutputParser):
    ai_prefix: str = "AI"  # change for salesperson_name
    verbose: bool = False

    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        if self.verbose:
            print("TEXT")
            print(text)
            print("-------")
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, text)
        if not match:
            return AgentFinish(
                {"output": text.split(f"{self.ai_prefix}:")[-1].strip()}, text
            )
        action = match.group(1)
        action_input = match.group(2)
        return AgentAction(action.strip(), action_input.strip(" ").strip('"'), text)

    @property
    def _type(self) -> str:
        return "sales-agent"
