"""
CrewAI Framework Benchmark Test
Tests CrewAI's ability to interact with MCP server
"""
import time
import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from utils import load_config, BenchmarkLogger
from mcp_jsonrpc_adapter import JSONRPCMCPClient

# Disable CrewAI telemetry and execution traces prompt
os.environ['CREWAI_TELEMETRY_OPT_OUT'] = 'true'
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'


def run_crewai_benchmark():
    """Run benchmark test for CrewAI framework"""
    
    # Initialize logger
    logger = BenchmarkLogger("CrewAI")
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
        
        # Initialize MCP Client and get tools
        step_start = time.time()
        mcp_client = JSONRPCMCPClient(config['mcp_server']['url'], timeout=30)
        mcp_client.initialize()
        available_tools = mcp_client.list_tools()
        logger.log_step("Initialize MCP Client", time.time() - step_start, 
                       f"Found {len(available_tools)} tools")
        
        # Execute MCP Query - Get pods list
        step_start = time.time()
        # Find the pods_list tool
        pods_tool = None
        for tool in available_tools:
            if 'pods_list' in tool['name']:
                pods_tool = tool['name']
                break
        
        if not pods_tool and available_tools:
            pods_tool = available_tools[0]['name']  # Fallback to first tool
        
        if pods_tool:
            mcp_response = mcp_client.call_tool(pods_tool, {})
        else:
            mcp_response = {"error": "No tools available"}
        
        logger.log_step("MCP Server Query", time.time() - step_start, 
                       f"Tool: {pods_tool if pods_tool else 'none'}")
        
        # Create Agent with MCP context
        step_start = time.time()
        kubernetes_agent = Agent(
            role='Kubernetes Administrator',
            goal='Analyze Kubernetes pod information and provide pod names',
            backstory=f'You are an expert Kubernetes administrator. You have access to pod data from the cluster.',
            verbose=False,
            llm=llm,
            allow_delegation=False
        )
        logger.log_step("Create Agent", time.time() - step_start)
        
        # Create Task with MCP data
        step_start = time.time()
        
        # Extract and limit MCP response content for faster processing
        if isinstance(mcp_response, dict) and 'content' in mcp_response:
            content_items = mcp_response['content']
            text_content = ""
            for item in content_items:
                if item.get('type') == 'text':
                    text_content += item.get('text', '')
            mcp_data_str = text_content[:2000]  # Limit to 2000 chars for speed
        else:
            mcp_data_str = str(mcp_response)[:2000]
        
        task = Task(
            description=f"""
            Based on the following data from the Kubernetes MCP server:
            
            {mcp_data_str}
            
            Task: {config['benchmark']['test_prompt']}
            
            Provide a clear list of pod names found in the cluster.
            """,
            agent=kubernetes_agent,
            expected_output="A clear list of pod names from the Kubernetes cluster"
        )
        logger.log_step("Create Task", time.time() - step_start)
        
        # Create Crew
        step_start = time.time()
        crew = Crew(
            agents=[kubernetes_agent],
            tasks=[task],
            verbose=False
        )
        logger.log_step("Create Crew", time.time() - step_start)
        
        # Run Crew with MCP data
        step_start = time.time()
        result = crew.kickoff()
        logger.log_step("Execute Crew Task", time.time() - step_start)
        
        # Total time
        total_time = logger.end()
        
        # Save results
        logger.save_results("results_crewai.json")
        
        print("\n[RESULT]")
        print(f"Final Result: {result}")
        
        return {
            "success": True,
            "total_time": total_time,
            "mcp_response": mcp_response,
            "result": str(result)
        }
        
    except Exception as e:
        logger.end()
        print(f"\n[ERROR] CrewAI benchmark failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = run_crewai_benchmark()
    print(f"\n[FINAL] CrewAI Benchmark {'Completed' if result['success'] else 'Failed'}")

