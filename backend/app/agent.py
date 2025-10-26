import os

from langchain_classic import hub
from langchain_classic.agents  import AgentExecutor, create_react_agent
from langchain_core.tools import render_text_description
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

try:
    from langchain.hub import pull
except ImportError:
    try:
        from langchain_classic import hub
        pull = hub.pull # Assign pull function if found via classic path
    except ImportError:
        # Fallback definition if hub cannot be imported at all (for local testing)
        print("Warning: langchain.hub module not found. Cannot pull prompts.")
        pull = None

from .tools import get_all_tools
from .prompt import instruction_addition, REACT_TEMPLATE_FALLBACK

import logging
logger = logging.getLogger('app.agent')

def create_security_agent():
    """
    Creates and returns the LangChain agent executor
    *** using the ReAct (Reasoning and Action) framework. ***
    """

    # FIXME: if ollama connection fails, the app fails.
    # this is a single point of failuer! Must have some resolution.
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    logger.info("ollama url is %s", ollama_base_url)

    llm_model = "qwen2.5-coder:32b"
    tools = get_all_tools()

    # init LLM
    # using qwen2.5-coder model as it allows the tool calling.
    # tried llama3, gemma3, deepseek-r1. not working good
    llm = ChatOllama(model=llm_model,
                     temperature=0,
                     base_url=ollama_base_url)

    # get the ReAct
    # pull from the hub. potential security risk if hub is compromised
    # envn hwchase17 is well known and trusted.
    # ref: https://medium.com/@yash9439/using-langchain-react-agents-with-qdrant-and-llama3-for-intelligent-information-retrieval-b181ce7a5962
    # Careful using it as it may have malicious code exec and prompt injection
    # Add fallback as this is a singpoint of failure
    try:
        if pull:
            logger.debug("Pull ReAct propmt from the langchain hub")
            base_prompt = hub.pull("hwchase17/react")
            template_string = base_prompt.template
        else:
            logger.warning("Use the hard coded local ReAct prompt")
            template_string = REACT_TEMPLATE_FALLBACK
    except Exception as e:
        logger.error(f"Error pulling ReAct prompt from hub ({e}). Using hardcoded local fallback.")
        template_string = REACT_TEMPLATE_FALLBACK

    tools_section_start = template_string.find("You have access to the following tools:")
    if tools_section_start != -1:
        modified_template_string = (
            template_string[:tools_section_start]
            + instruction_addition
            + template_string[tools_section_start:]
        )
    else:
        logger.error("Warning: Could not find expected tool section in ReAct prompt. Adding instructions at the beginning.")
        modified_template_string = instruction_addition + template_string

    tool_strings = render_text_description(tools)
    tool_names = ", ".join([t.name for t in tools])
    prompt = PromptTemplate.from_template(modified_template_string)

    # partial the prompt with these rendered tool strings
    prompt = prompt.partial(
        tools=tool_strings,
        tool_names=tool_names,
    )

    # bind stop generating text when it sees "Observation:"
    llm_with_stop = llm.bind(stop=["\nObservation:"])
    agent = create_react_agent(
        llm=llm_with_stop,
        tools=tools,
        prompt=prompt
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )

    logger.info("Security agent (Ollama/Qwen2.5-Coder using ReAct) created successfully.")
    return agent_executor


# import os
# from typing import Annotated
# # --- FIXED IMPORT ---
# from langchain.agents import create_react_agent
# from langchain_core.agents import AgentExecutor # Moved from langchain.agents
# # --- END FIXED IMPORT ---
# from langchain_ollama import ChatOllama
# from langchain_core.tools import render_text_description, InjectedToolArg
# from langchain_classic import hub
# from app.tools import get_all_tools
# from langchain_core.prompts import PromptTemplate

# def create_security_agent():
#     """
#     Creates and returns the LangChain agent executor
#     using the ReAct (Reasoning and Action) framework.
#     """

#     tools = get_all_tools()

#     # Read OLLAMA_BASE_URL from environment set by Docker Compose
#     # Fallback to localhost for direct local development runs
#     ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

#     # 2. Initialize the LLM, explicitly passing the base URL
#     llm = ChatOllama(
#         model="qwen2.5-coder:32b",
#         temperature=0,
#         base_url=ollama_base_url
#     )

#     # --- Customize the ReAct Prompt for general questions ---
#     base_prompt = hub.pull("hwchase17/react")
#     template_string = base_prompt.template
#     instruction_addition = """
#     IMPORTANT: If the user asks a general question about your capabilities, purpose, or asks for help in a general way (e.g., "What can you do?", "Help me", "Who are you?"), answer directly based on your role as a 'Security Incident Knowledge Assistant' without using any tools. Only use tools if the question is specifically about security policies, procedures, or security logs.
#     """

#     # Inject instruction before the tool definition section
#     tools_section_start = template_string.find("You have access to the following tools:")
#     if tools_section_start != -1:
#         modified_template_string = (
#             template_string[:tools_section_start]
#             + instruction_addition
#             + template_string[tools_section_start:]
#         )
#     else:
#         modified_template_string = instruction_addition + template_string

#     prompt = PromptTemplate.from_template(modified_template_string)
#     # --- End Prompt Customization ---


#     # 3. Render tools and partial the prompt
#     tool_strings = render_text_description(tools)
#     tool_names = ", ".join([t.name for t in tools])
#     prompt = prompt.partial(
#         tools=tool_strings,
#         tool_names=tool_names,
#     )

#     # 4. Bind the LLM to stop generating text when it encounters "Observation:"
#     # This is CRITICAL for ReAct execution
#     llm_with_stop = llm.bind(stop=["\nObservation:"])

#     # 5. Create the Agent
#     agent = create_react_agent(
#         llm=llm_with_stop,
#         tools=tools,
#         prompt=prompt
#     )

#     # 6. Create the Agent Executor with safety features
#     agent_executor = AgentExecutor(
#         agent=agent,
#         tools=tools,
#         verbose=True,
#         max_iterations=5,
#         handle_parsing_errors=True
#     )

#     print("Security agent (Ollama/Qwen2.5-Coder using ReAct) created successfully.")
#     return agent_executor