"""
LangGraph Framework Benchmark Test
Tests LangGraph's ability to interact with MCP server
"""
import time
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from utils import load_config, BenchmarkLogger
from mcp_jsonrpc_adapter import JSONRPCMCPClient


class GraphState(TypedDict):
    """State for the graph"""
    messages: list
    mcp_data: dict
    final_result: str


def run_langgraph_benchmark():
    """Run benchmark test for LangGraph framework"""
    
    # Initialize logger
    logger = BenchmarkLogger("LangGraph")
    logger.start()
    
    try:
        # Load configuration
        step_start = time.time()
        config = load_config()
        logger.log_step("Load Configuration", time.time() - step_start)
        
        # Initialize OpenAI (API key is set in environment by load_config)
        step_start = time.time()
        llm = ChatOpenAI(
            model=config['openai']['model'],
            temperature=config['openai']['temperature']
        )
        logger.log_step("Initialize OpenAI", time.time() - step_start)
        
        # Initialize MCP Client
        step_start = time.time()
        mcp_client = JSONRPCMCPClient(config['mcp_server']['url'], timeout=30)
        mcp_client.initialize()
        available_tools = mcp_client.list_tools()
        logger.log_step("Initialize MCP Client", time.time() - step_start,
                       f"Found {len(available_tools)} tools")
        
        # Find pods_list tool
        pods_tool = None
        for tool in available_tools:
            if 'pods_list' in tool['name']:
                pods_tool = tool['name']
                break
        if not pods_tool and available_tools:
            pods_tool = available_tools[0]['name']
        
        # Define nodes
        def query_mcp_node(state: GraphState) -> GraphState:
            """Node to query MCP server"""
            step_start = time.time()
            
            # Use pods_list tool
            if pods_tool:
                mcp_response = mcp_client.call_tool(pods_tool, {})
            else:
                mcp_response = {"error": "No tools available"}
            
            logger.log_step("MCP Server Query (Node)", time.time() - step_start,
                           f"Tool: {pods_tool if pods_tool else 'none'}")
            
            state['mcp_data'] = mcp_response
            state['messages'].append(
                HumanMessage(content=f"I received data from Kubernetes MCP server for: {config['benchmark']['test_prompt']}")
            )
            return state
        
        def process_with_llm_node(state: GraphState) -> GraphState:
            """Node to process MCP data with LLM"""
            step_start = time.time()
            
            # Extract content from MCP response
            mcp_data = state['mcp_data']
            if isinstance(mcp_data, dict) and 'content' in mcp_data:
                content_items = mcp_data['content']
                text_content = ""
                for item in content_items:
                    if item.get('type') == 'text':
                        text_content += item.get('text', '')
                mcp_data_str = text_content
            else:
                mcp_data_str = str(mcp_data)
            
            prompt = f"""
            I queried a Kubernetes cluster via MCP server with the request: "{config['benchmark']['test_prompt']}"
            
            The MCP server response contains pod information:
            {mcp_data_str[:2000]}...
            
            Please provide a clear summary of the pod names found.
            """
            
            response = llm.invoke([HumanMessage(content=prompt)])
            logger.log_step("LLM Processing (Node)", time.time() - step_start)
            
            state['messages'].append(AIMessage(content=response.content))
            state['final_result'] = response.content
            return state
        
        # Build graph
        step_start = time.time()
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("query_mcp", query_mcp_node)
        workflow.add_node("process_llm", process_with_llm_node)
        
        # Add edges
        workflow.set_entry_point("query_mcp")
        workflow.add_edge("query_mcp", "process_llm")
        workflow.add_edge("process_llm", END)
        
        # Compile
        app = workflow.compile()
        logger.log_step("Build & Compile Graph", time.time() - step_start)
        
        # Execute graph
        step_start = time.time()
        initial_state: GraphState = {
            "messages": [HumanMessage(content=config['benchmark']['test_prompt'])],
            "mcp_data": {},
            "final_result": ""
        }
        
        final_state = app.invoke(initial_state)
        logger.log_step("Execute Graph", time.time() - step_start)
        
        # Total time
        total_time = logger.end()
        
        # Save results
        logger.save_results("results_langgraph.json")
        
        print("\n[RESULT]")
        print(f"Final Result: {final_state['final_result']}")
        
        return {
            "success": True,
            "total_time": total_time,
            "mcp_data": final_state['mcp_data'],
            "result": final_state['final_result']
        }
        
    except Exception as e:
        logger.end()
        print(f"\n[ERROR] LangGraph benchmark failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = run_langgraph_benchmark()
    print(f"\n[FINAL] LangGraph Benchmark {'Completed' if result['success'] else 'Failed'}")

