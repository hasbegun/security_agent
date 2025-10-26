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
