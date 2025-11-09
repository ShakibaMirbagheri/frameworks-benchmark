"""
Quick test script to verify MCP connection
"""
from mcp_jsonrpc_adapter import JSONRPCMCPClient, test_jsonrpc_server
from utils import load_config

def main():
    print("="*60)
    print("MCP Connection Test")
    print("="*60)
    
    # Load config
    config = load_config()
    server_url = config['mcp_server']['url']
    
    print(f"\nTesting connection to: {server_url}")
    
    # Quick test
    is_connected, error = test_jsonrpc_server(server_url, timeout=10)
    
    if is_connected:
        print("✅ Connection successful!")
        
        # Get detailed info
        print("\nGetting server details...")
        client = JSONRPCMCPClient(server_url, timeout=30)
        client.initialize()
        
        tools = client.list_tools()
        print(f"\n📋 Available Tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            name = tool.get('name', 'Unknown')
            desc = tool.get('description', 'No description')
            print(f"  {i}. {name}")
            print(f"     {desc}")
        
        # Try calling first tool
        if tools:
            print(f"\n🔧 Testing first tool: {tools[0]['name']}")
            try:
                result = client.call_tool(tools[0]['name'], {})
                print(f"✅ Tool execution successful!")
                print(f"Result: {str(result)[:200]}...")
            except Exception as e:
                print(f"❌ Tool execution failed: {e}")
    else:
        print(f"❌ Connection failed: {error}")
        print("\nTroubleshooting:")
        print("1. Check if the MCP server URL is correct in config.yaml")
        print("2. Verify network connectivity to the server")
        print("3. Check if the server is running and accessible")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

