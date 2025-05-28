#!/usr/bin/env python3
"""
Example LangGraph Agent using Wetland Data Tools

This example demonstrates how to create a LangGraph agent that can:
- Query comprehensive wetland data for any coordinates
- Generate detailed wetland maps with high resolution
- Generate overview wetland maps for regional context
- Generate adaptive wetland maps with intelligent buffer sizing
- Generate custom wetland maps with specified parameters

The agent can understand natural language requests and automatically
call the appropriate tools with the correct coordinates and parameters.
"""

import os
from typing import Annotated
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from tools import WETLAND_TOOLS, get_tool_descriptions
import uuid

def create_wetland_agent():
    """Create a LangGraph agent with wetland data tools"""
    
    # Use Google Gemini which supports tool calling
    # Make sure to set your API key: export GOOGLE_API_KEY="your-key-here"
    # You can also use other supported models:
    # - "openai:gpt-4o-mini" (export OPENAI_API_KEY="sk-...")
    # - "anthropic:claude-3-5-haiku-latest" (export ANTHROPIC_API_KEY="sk-...")
    
    model = "google_genai:gemini-2.5-flash-preview-04-17"
    memory = MemorySaver()
    # Create the agent with our wetland tools
    agent = create_react_agent(
        model=model,
        tools=WETLAND_TOOLS,
        checkpointer=memory,
        prompt="""You are a wetland data specialist agent. You help users analyze wetland data and generate professional wetland maps for any location.

Available tools:
- query_wetland_data: Query comprehensive wetland data from USFWS NWI, EPA RIBITS, and other sources
- generate_overview_wetland_map: Generate regional overview map (1.0 mile buffer, topographic base)
- generate_adaptive_wetland_map: Generate intelligent map with optimal buffer sizing based on analysis
- generate_custom_wetland_map: Generate custom map with user-specified buffer, base map, and transparency

When users ask about wetland data for a location:
1. First query the wetland data to understand what wetlands are present
2. Explain the progressive search strategy (exact location → 0.5 mile → 1.0 mile radius)
3. Provide detailed NWI classifications and regulatory implications
4. Offer to generate appropriate maps based on the analysis results
5. Always provide coordinates in the format (longitude, latitude)

Key information to provide:
- Wetland types and NWI classifications
- Distance to nearest wetlands if not at exact location
- Environmental significance and regulatory status
- Recommendations for next steps

For Puerto Rico examples, use coordinates around (-66.199399, 18.408303).
For Florida Everglades examples, use coordinates around (-80.8431, 25.4663).

Be helpful and explain what each map type shows, when to use them, and their regulatory implications."""
    )
    
    return agent

def main():
    """Example usage of the wetland agent"""
    
    print("🌿 Wetland Data Agent Example")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set your GOOGLE_API_KEY environment variable")
        print("   export GOOGLE_API_KEY='your-key-here'")
        print("   Or change the model in create_wetland_agent() to use a different provider")
        return
    
    # Create the agent
    try:
        agent = create_wetland_agent()
        print("✅ Agent created successfully!")
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return
    
    # Example queries
    example_queries = [
        "What wetland data is available for Bayamón, Puerto Rico at coordinates -66.199399, 18.408303?",
        "I need an adaptive wetland map that automatically determines the best buffer size for longitude -66.199399, latitude 18.408303",
        "Can you create a custom wetland map for the Everglades with a 2-mile buffer and topographic base map?",
        "Analyze wetlands at coordinates -80.8431, 25.4663 in the Florida Everglades",
        "What are the regulatory implications for development at coordinates -66.199399, 18.408303?",
        "Generate an overview map for regional wetland context in Puerto Rico"
    ]
    
    print(f"\n📋 Available Tools:")
    descriptions = get_tool_descriptions()
    for tool_name, description in descriptions.items():
        print(f"   • {tool_name}: {description}")
    
    print(f"\n🌍 Data Sources:")
    print(f"   • USFWS National Wetlands Inventory (NWI)")
    print(f"   • EPA RIBITS (Regulatory tracking)")
    print(f"   • EPA National Hydrography Dataset (NHD)")
    print(f"   • USFWS Riparian Mapping")
    
    print(f"\n🎯 Example Queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"   {i}. {query}")
    
    # Interactive mode
    print(f"\n💬 Interactive Mode (type 'quit' to exit):")
    print(f"   Try asking about wetland data for any location!")
    print(f"   Example: 'What wetlands are near Miami, Florida?'")
    print(f"   Example: 'Generate a wetland map for my property at [coordinates]'")
    
    while True:
        try:
            user_input = input(f"\n🤔 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 Agent is working...")
            
            # Run the agent
            response = agent.invoke({
                "messages": [HumanMessage(content=user_input)]
            }, config={"configurable": {"thread_id": str(uuid.uuid4())}})
            
            # Print the agent's response
            last_message = response["messages"][-1]
            print(f"\n🌿 Agent Response:")
            print(f"{last_message.content}")
            
        except KeyboardInterrupt:
            print(f"\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"Please try again or type 'quit' to exit.")

def run_example_query():
    """Run a single example query without interactive mode"""
    
    print("🌿 Running Example Query")
    print("=" * 30)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set your GOOGLE_API_KEY environment variable")
        print("   export GOOGLE_API_KEY='your-key-here'")
        print("   Or change the model in create_wetland_agent() to use a different provider")
        return
    
    try:
        agent = create_wetland_agent()
        
        # Example query
        query = "What wetland data is available in Puerto Rico at coordinates 18.434059, -66.150906?"
        print(f"Query: {query}")
        print(f"\n🤖 Agent Response:")
        
        response = agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        last_message = response["messages"][-1]
        print(last_message.content)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_comprehensive_example():
    """Run a comprehensive example with multiple tool calls"""
    
    print("🌿 Running Comprehensive Wetland Analysis Example")
    print("=" * 50)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set your GOOGLE_API_KEY environment variable")
        return
    
    try:
        agent = create_wetland_agent()
        
        # Comprehensive query
        query = """I'm planning a development project at coordinates 18.434059, -66.150906 in Puerto Rico. 
        Please analyze the wetland data for this location and generate an appropriate map. 
        I need to understand any regulatory implications and what permits might be required."""
        
        print(f"Query: {query}")
        print(f"\n🤖 Agent working on comprehensive analysis...")
        
        response = agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        last_message = response["messages"][-1]
        print(f"\n🌿 Comprehensive Analysis Result:")
        print(f"{last_message.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_map_generation_example():
    """Run an example focused on map generation"""
    
    print("🌿 Running Map Generation Example")
    print("=" * 40)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Please set your GOOGLE_API_KEY environment variable")
        return
    
    try:
        agent = create_wetland_agent()
        
        # Map generation query
        query = """Create a custom wetland map for coordinates 18.434059, -66.150906
. 
        Use a 1.5 mile buffer with satellite imagery base map and 0.7 transparency for the wetland layers. 
        This is for an environmental assessment report."""
        
        print(f"Query: {query}")
        print(f"\n🤖 Agent generating custom map...")
        
        response = agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        last_message = response["messages"][-1]
        print(f"\n🗺️  Map Generation Result:")
        print(f"{last_message.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--example":
            run_example_query()
        elif sys.argv[1] == "--comprehensive":
            run_comprehensive_example()
        elif sys.argv[1] == "--maps":
            run_map_generation_example()
        else:
            print("Usage:")
            print("  python wetlands_agent.py                # Interactive mode")
            print("  python wetlands_agent.py --example      # Simple example query")
            print("  python wetlands_agent.py --comprehensive # Comprehensive analysis example")
            print("  python wetlands_agent.py --maps         # Map generation example")
    else:
        main() 