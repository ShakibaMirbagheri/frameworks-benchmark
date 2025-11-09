# AI Framework Benchmark Suite

A comprehensive benchmarking suite for testing and comparing AI frameworks (CrewAI, LangGraph, DSPy, and Langchain) with MCP (Model Context Protocol) server integration.

## Overview

This project benchmarks the performance of four popular AI frameworks when interacting with a Kubernetes MCP server. Each framework is tested with the same task: querying pod names from a Kubernetes cluster via JSON-RPC v2 protocol.

## Frameworks Tested

1. **CrewAI** - Multi-agent orchestration framework
2. **LangGraph** - State machine-based workflow framework
3. **DSPy** - Declarative programming for language models
4. **Langchain** - Comprehensive framework for LLM applications

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Access to MCP server at https://mcp.n3s.ai

## Installation

1. Clone or navigate to this directory:
```bash
cd /home/mohmd/Documents/Shakiba/Frameworks
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Edit `config.yaml` and add your OpenAI API key:

```yaml
openai:
  api_key: "your-openai-api-key-here"
  model: "gpt-4"
  temperature: 0.7
```

The MCP server URL is already configured, but you can modify it if needed.

## Usage

### Run All Benchmarks

To run all framework benchmarks and generate a comparison report:

```bash
python run_benchmark.py
```

This will:
- Run each framework test sequentially
- Log timing for each step
- Generate a comparison report
- Save results to `benchmark_report.json`

### Run Individual Framework Tests

You can also run tests for individual frameworks:

```bash
# Test CrewAI
python test_crewai.py

# Test LangGraph
python test_langgraph.py

# Test DSPy
python test_dspy.py

# Test Langchain
python test_langchain.py
```

## Output Files

After running the benchmarks, you'll find:

- `results_crewai.json` - Detailed CrewAI results
- `results_langgraph.json` - Detailed LangGraph results
- `results_dspy.json` - Detailed DSPy results
- `results_langchain.json` - Detailed Langchain results
- `benchmark_report.json` - Complete comparison report

## Benchmark Metrics

Each framework is measured on:

1. **Configuration Load Time** - Time to load config.yaml
2. **OpenAI Initialization** - Time to set up LLM connection
3. **MCP Client Initialization** - Time to initialize MCP client
4. **MCP Query Time** - Time to query MCP server via JSON-RPC v2
5. **Framework-Specific Steps** - Agent/workflow creation and execution
6. **Total Time** - End-to-end execution time

## Understanding the Results

The benchmark report includes:

### Summary Table
Shows success status and total time for each framework

### Detailed Step Timing
Breaks down each framework's execution into individual steps with timing

### Performance Ranking
Ranks successful frameworks by total execution time (fastest to slowest)

## Example Output

```
==================================================================
BENCHMARK COMPARISON REPORT
==================================================================

📊 SUMMARY TABLE
+-----------+---------+-------------+-------+
| Framework | Success | Total Time  | Error |
+-----------+---------+-------------+-------+
| CrewAI    | ✓       | 3.4521s    | -     |
| LangGraph | ✓       | 2.8934s    | -     |
| DSPy      | ✓       | 2.1234s    | -     |
| Langchain | ✓       | 3.2145s    | -     |
+-----------+---------+-------------+-------+

🏆 PERFORMANCE RANKING (by total time)
+------+-----------+----------+
| Rank | Framework | Time     |
+------+-----------+----------+
| 1    | DSPy      | 2.1234s  |
| 2    | LangGraph | 2.8934s  |
| 3    | Langchain | 3.2145s  |
| 4    | CrewAI    | 3.4521s  |
+------+-----------+----------+
```

## Project Structure

```
.
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── mcp_client.py           # MCP JSON-RPC v2 client
├── utils.py                # Utility functions and logging
├── test_crewai.py          # CrewAI benchmark
├── test_langgraph.py       # LangGraph benchmark
├── test_dspy.py            # DSPy benchmark
├── test_langchain.py       # Langchain benchmark
├── run_benchmark.py        # Main benchmark runner
└── README.md               # This file
```

## Troubleshooting

### Issue: Import errors
**Solution**: Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: MCP server connection failed
**Solution**: 
- Check that the MCP server URL is correct in `config.yaml`
- Verify network connectivity to https://mcp.n3s.ai
- Check firewall settings

### Issue: OpenAI API errors
**Solution**:
- Verify your API key is correct in `config.yaml`
- Check your OpenAI account has sufficient credits
- Ensure the model name is valid (e.g., "gpt-4" or "gpt-3.5-turbo")

### Issue: Timeout errors
**Solution**:
- Increase timeout in `run_benchmark.py` (default is 120 seconds)
- Check network latency to MCP server
- Try with a simpler/faster OpenAI model

## Customization

### Change Test Prompt

Edit `config.yaml`:
```yaml
benchmark:
  test_prompt: "your custom prompt here"
```

### Adjust Timeout

Edit `run_benchmark.py`:
```python
result = subprocess.run(
    [sys.executable, test_file],
    capture_output=True,
    text=True,
    timeout=300  # Change to desired timeout in seconds
)
```

### Add Custom Metrics

Modify `BenchmarkLogger` in `utils.py` to track additional metrics.

## Notes

- All timing measurements are in seconds with 4 decimal precision
- Each framework test runs independently to avoid interference
- Results may vary based on network conditions and OpenAI API response times
- The MCP server must support JSON-RPC v2 protocol

## License

This benchmark suite is provided as-is for testing and evaluation purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review individual framework documentation
3. Verify MCP server is operational

