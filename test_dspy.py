"""
DSPy Framework Benchmark Test
Tests DSPy's ability to interact with MCP server
"""
import time
import dspy
from utils import load_config, BenchmarkLogger
from mcp_jsonrpc_adapter import JSONRPCMCPClient


class KubernetesPodQuery(dspy.Signature):
    """Query Kubernetes pods and provide summary"""
    
    mcp_data = dspy.InputField(desc="Raw data from MCP server")
    query = dspy.InputField(desc="User query about pods")
    answer = dspy.OutputField(desc="Summarized answer about pod names")


class PodQueryModule(dspy.Module):
    """Module for querying pods via MCP"""
    
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThought(KubernetesPodQuery)
    
    def forward(self, mcp_data, query):
        return self.generate_answer(mcp_data=str(mcp_data), query=query)


def run_dspy_benchmark():
    """Run benchmark test for DSPy framework"""
    
    # Initialize logger
    logger = BenchmarkLogger("DSPy")
    logger.start()
    
    try:
        # Load configuration
        step_start = time.time()
        config = load_config()
        logger.log_step("Load Configuration", time.time() - step_start)
        
        # Initialize DSPy with OpenAI (API key is set in environment by load_config)
        step_start = time.time()
        # DSPy 2.0+ uses LM class instead of OpenAI
        import os
        lm = dspy.LM(
            model=f"openai/{config['openai']['model']}",
            api_key=os.environ.get('OPENAI_API_KEY'),
            temperature=config['openai']['temperature']
        )
        dspy.configure(lm=lm)
        logger.log_step("Initialize DSPy + OpenAI", time.time() - step_start)
        
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
        
        # Query MCP Server
        step_start = time.time()
        if pods_tool:
            mcp_response = mcp_client.call_tool(pods_tool, {})
        else:
            mcp_response = {"error": "No tools available"}
        logger.log_step("MCP Server Query", time.time() - step_start,
                       f"Tool: {pods_tool if pods_tool else 'none'}")
        
        # Initialize Module
        step_start = time.time()
        pod_query = PodQueryModule()
        logger.log_step("Initialize DSPy Module", time.time() - step_start)
        
        # Execute Query
        step_start = time.time()
        
        # Extract content from MCP response
        if isinstance(mcp_response, dict) and 'content' in mcp_response:
            content_items = mcp_response['content']
            text_content = ""
            for item in content_items:
                if item.get('type') == 'text':
                    text_content += item.get('text', '')
            mcp_data_str = text_content[:2000]  # Limit length
        else:
            mcp_data_str = str(mcp_response)[:2000]
        
        result = pod_query(
            mcp_data=mcp_data_str,
            query=config['benchmark']['test_prompt']
        )
        logger.log_step("Execute DSPy Query", time.time() - step_start)
        
        # Total time
        total_time = logger.end()
        
        # Save results
        logger.save_results("results_dspy.json")
        
        print("\n[RESULT]")
        print(f"Final Result: {result.answer}")
        
        return {
            "success": True,
            "total_time": total_time,
            "mcp_response": mcp_response,
            "result": result.answer
        }
        
    except Exception as e:
        logger.end()
        print(f"\n[ERROR] DSPy benchmark failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = run_dspy_benchmark()
    print(f"\n[FINAL] DSPy Benchmark {'Completed' if result['success'] else 'Failed'}")

