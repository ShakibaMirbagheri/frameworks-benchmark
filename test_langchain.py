"""
Langchain Framework Benchmark Test
Tests Langchain's ability to interact with MCP server
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import load_config, BenchmarkLogger
from mcp_jsonrpc_adapter import JSONRPCMCPClient


def run_langchain_benchmark():
    """Run benchmark test for Langchain framework"""
    
    # Initialize logger
    logger = BenchmarkLogger("Langchain")
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
        
        # Initialize MCP Client and Get Tools
        step_start = time.time()
        mcp_client = JSONRPCMCPClient(config['mcp_server']['url'], timeout=30)
        mcp_client.initialize()
        logger.log_step("Initialize MCP Client", time.time() - step_start)
        
        # List available tools
        step_start = time.time()
        available_tools_list = mcp_client.list_tools()
        logger.log_step("List MCP Tools", time.time() - step_start,
                       f"Found {len(available_tools_list)} tools")
        
        # Find pods_list tool
        pods_tool = None
        for tool in available_tools_list:
            if 'pods_list' in tool['name']:
                pods_tool = tool['name']
                break
        if not pods_tool and available_tools_list:
            pods_tool = available_tools_list[0]['name']
        
        # Query MCP Server directly for benchmark
        step_start = time.time()
        if pods_tool:
            mcp_response = mcp_client.call_tool(pods_tool, {})
        else:
            mcp_response = {"error": "No tools available"}
        logger.log_step("MCP Server Query", time.time() - step_start,
                       f"Tool: {pods_tool if pods_tool else 'none'}")
        
        # Use LangChain Expression Language (LCEL) chain
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
        
        prompt_template = ChatPromptTemplate.from_template("""
        Based on the following data from Kubernetes MCP server:
        {mcp_data}
        
        Answer this query: {query}
        
        Provide a clear and concise list of pod names.
        """)
        
        chain = prompt_template | llm | StrOutputParser()
        chain_result = chain.invoke({
            "mcp_data": mcp_data_str,
            "query": config['benchmark']['test_prompt']
        })
        logger.log_step("Execute LLM Chain", time.time() - step_start)
        
        # Total time
        total_time = logger.end()
        
        # Save results
        logger.save_results("results_langchain.json")
        
        print("\n[RESULT]")
        print(f"Final Result: {chain_result}")
        
        return {
            "success": True,
            "total_time": total_time,
            "mcp_response": mcp_response,
            "result": chain_result
        }
        
    except Exception as e:
        logger.end()
        print(f"\n[ERROR] Langchain benchmark failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = run_langchain_benchmark()
    print(f"\n[FINAL] Langchain Benchmark {'Completed' if result['success'] else 'Failed'}")

