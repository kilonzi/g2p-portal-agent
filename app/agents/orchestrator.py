from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from .prompts import ROUTER_AGENT_PROMPT
from .specialists import genetic_discovery_agent, structural_biology_agent, variant_analyst_agent
from .model import get_model

# 1. Thread Persistence (Short-term memory of the conversation)
checkpointer = MemorySaver()

# 2. Universal Store (Long-term memory across threads)
store = InMemoryStore()

# 3. Backend Routing
def backend_factory(rt):
    """
    Routes file operations:
    - /memories/ -> StoreBackend (Persistent)
    - *          -> StateBackend (Ephemeral)
    """
    return CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}
    )

router_agent = create_deep_agent(
    model=get_model(),
    system_prompt=ROUTER_AGENT_PROMPT,
    subagents=[genetic_discovery_agent, structural_biology_agent, variant_analyst_agent],
    checkpointer=checkpointer,
    store=store,
    backend=backend_factory
)
