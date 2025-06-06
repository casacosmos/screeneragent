#!/usr/bin/env python3
"""
Async Environmental Agent using LangGraph

This agent provides asynchronous environmental analysis capabilities
using modern LangGraph patterns and async tools.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# Import our async environmental tools
from async_environmental_tools import (
    ASYNC_ENVIRONMENTAL_TOOLS,
    EnvironmentalState,
    analyze_wetlands_async,
    analyze_nonattainment_async,
    analyze_flood_risk_async,
    analyze_critical_habitat_async,
    analyze_karst_async,
    comprehensive_environmental_analysis_async
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncEnvironmentalAgent:
    """
    Async Environmental Analysis Agent using LangGraph
    
    This agent can perform environmental analyses asynchronously,
    managing state and coordinating multiple analysis tools.
    """
    
    def __init__(self, checkpointer=None):
        """Initialize the async environmental agent"""
        self.checkpointer = checkpointer or MemorySaver()
        self.tools = ASYNC_ENVIRONMENTAL_TOOLS
        self.tool_node = ToolNode(self.tools)
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for environmental analysis"""
        
        # Create the state graph
        workflow = StateGraph(EnvironmentalState)
        
        # Define nodes
        workflow.add_node("start_analysis", self._start_analysis_node)
        workflow.add_node("coordinate_analysis", self._coordinate_analysis_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Define edges
        workflow.add_edge("start_analysis", "coordinate_analysis")
        workflow.add_conditional_edges(
            "coordinate_analysis",
            self._should_use_tools,
            {
                "tools": "tools",
                "finalize": "finalize_results"
            }
        )
        workflow.add_edge("tools", "finalize_results")
        workflow.add_edge("finalize_results", END)
        
        # Set entry point
        workflow.set_entry_point("start_analysis")
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _start_analysis_node(self, state: EnvironmentalState) -> EnvironmentalState:
        """Initialize the analysis session"""
        logger.info("Starting environmental analysis session")
        
        # Initialize analysis results if not present
        if "analysis_results" not in state:
            state["analysis_results"] = {}
        
        # Add system message if no messages present
        if not state.get("messages"):
            state["messages"] = [
                AIMessage(content="Environmental analysis agent initialized. Ready to process analysis requests.")
            ]
        
        return state
    
    async def _coordinate_analysis_node(self, state: EnvironmentalState) -> EnvironmentalState:
        """Coordinate the analysis workflow"""
        logger.info("Coordinating analysis workflow")
        
        # Check if we have a location to analyze
        if state.get("analysis_location"):
            longitude, latitude = state["analysis_location"]
            project_name = state.get("project_name", "Environmental_Analysis")
            
            # Add message indicating analysis start
            state["messages"].append(
                AIMessage(content=f"Starting comprehensive environmental analysis for {project_name} at coordinates {longitude}, {latitude}")
            )
        
        return state
    
    def _should_use_tools(self, state: EnvironmentalState) -> Literal["tools", "finalize"]:
        """Determine if tools should be used based on state"""
        
        # Check if we have location data and haven't run analysis yet
        if (state.get("analysis_location") and 
            not state.get("analysis_results", {}).get("comprehensive_complete")):
            return "tools"
        
        return "finalize"
    
    async def _finalize_results_node(self, state: EnvironmentalState) -> EnvironmentalState:
        """Finalize and summarize the analysis results"""
        logger.info("Finalizing analysis results")
        
        analysis_results = state.get("analysis_results", {})
        
        # Create summary
        summary = {
            "session_complete": True,
            "total_analyses": len(analysis_results),
            "successful_analyses": len([r for r in analysis_results.values() 
                                      if isinstance(r, dict) and r.get("status") != "error"]),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add final message
        state["messages"].append(
            AIMessage(content=f"Environmental analysis session completed. {summary}")
        )
        
        state["analysis_results"]["session_summary"] = summary
        
        return state
    
    async def run_analysis(self, 
                          longitude: float, 
                          latitude: float,
                          project_name: str = "Environmental_Analysis",
                          config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Run a comprehensive environmental analysis
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            project_name: Name for the analysis project
            config: Optional runtime configuration
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Running async environmental analysis for {project_name}")
            
            # Create initial state
            initial_state = EnvironmentalState(
                messages=[
                    HumanMessage(content=f"Analyze environmental conditions at {longitude}, {latitude} for project {project_name}")
                ],
                project_name=project_name,
                analysis_location=(longitude, latitude),
                analysis_results={}
            )
            
            # Generate a thread ID for this analysis session
            thread_id = f"env_analysis_{int(datetime.now().timestamp())}"
            
            config = config or RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            
            # Run the comprehensive analysis tool directly
            result = await comprehensive_environmental_analysis_async(
                longitude=longitude,
                latitude=latitude,
                project_name=project_name,
                state=initial_state,
                config=config
            )
            
            # Parse the JSON result
            analysis_data = json.loads(result)
            
            logger.info(f"Analysis completed with status: {analysis_data.get('status')}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_individual_analysis(self,
                                    analysis_type: str,
                                    longitude: float,
                                    latitude: float,
                                    **kwargs) -> Dict[str, Any]:
        """
        Run an individual environmental analysis
        
        Args:
            analysis_type: Type of analysis ('wetlands', 'nonattainment', 'flood', 'critical_habitat', 'karst')
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            **kwargs: Additional arguments for specific analysis types
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Running {analysis_type} analysis at {longitude}, {latitude}")
            
            # Select the appropriate tool
            if analysis_type == "wetlands":
                result = await analyze_wetlands_async(
                    longitude=longitude,
                    latitude=latitude,
                    **kwargs
                )
            elif analysis_type == "nonattainment":
                result = await analyze_nonattainment_async(
                    longitude=longitude,
                    latitude=latitude,
                    **kwargs
                )
            elif analysis_type == "flood":
                result = await analyze_flood_risk_async(
                    longitude=longitude,
                    latitude=latitude,
                    **kwargs
                )
            elif analysis_type == "critical_habitat":
                result = await analyze_critical_habitat_async(
                    longitude=longitude,
                    latitude=latitude,
                    **kwargs
                )
            elif analysis_type == "karst":
                result = await analyze_karst_async(
                    longitude=longitude,
                    latitude=latitude,
                    **kwargs
                )
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}. Supported types: wetlands, nonattainment, flood, critical_habitat, karst")
            
            # Parse the JSON result
            analysis_data = json.loads(result)
            
            logger.info(f"{analysis_type} analysis completed with status: {analysis_data.get('status')}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"{analysis_type} analysis failed: {e}")
            return {
                "analysis_type": analysis_type,
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def batch_analysis(self,
                           locations: List[Dict[str, Any]],
                           project_name: str = "Batch_Environmental_Analysis") -> List[Dict[str, Any]]:
        """
        Run environmental analyses for multiple locations concurrently
        
        Args:
            locations: List of location dictionaries with 'longitude', 'latitude', and optional 'name'
            project_name: Base name for the analysis project
            
        Returns:
            List of analysis results for each location
        """
        try:
            logger.info(f"Starting batch analysis for {len(locations)} locations")
            
            # Create tasks for concurrent execution
            tasks = []
            for i, location in enumerate(locations):
                longitude = location['longitude']
                latitude = location['latitude']
                location_name = location.get('name', f"Location_{i+1}")
                
                task = self.run_analysis(
                    longitude=longitude,
                    latitude=latitude,
                    project_name=f"{project_name}_{location_name}"
                )
                tasks.append(task)
            
            # Execute all analyses concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "location_index": i,
                        "location": locations[i],
                        "status": "error",
                        "error_message": str(result),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    result["location_index"] = i
                    result["location"] = locations[i]
                    processed_results.append(result)
            
            logger.info(f"Batch analysis completed: {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return [{
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }]


# Example usage and testing
async def main():
    """Example usage of the async environmental agent"""
    
    # Create the agent
    agent = AsyncEnvironmentalAgent()
    
    # Test coordinates (example location in Puerto Rico)
    longitude = -66.7135
    latitude = 18.4058
    
    print("🚀 Testing Async Environmental Agent")
    print("=" * 50)
    
    # Test comprehensive analysis
    print(f"\n📍 Running comprehensive analysis at {longitude}, {latitude}")
    result = await agent.run_analysis(
        longitude=longitude,
        latitude=latitude,
        project_name="Test_Async_Analysis"
    )
    
    print(f"✅ Analysis Status: {result.get('status')}")
    print(f"📊 Summary: {result.get('summary', {})}")
    
    # Test individual analysis
    print(f"\n🌿 Running wetlands analysis")
    wetland_result = await agent.run_individual_analysis(
        analysis_type="wetlands",
        longitude=longitude,
        latitude=latitude
    )
    
    print(f"✅ Wetlands Status: {wetland_result.get('status')}")
    
    # Test critical habitat analysis
    print(f"\n🦎 Running critical habitat analysis")
    habitat_result = await agent.run_individual_analysis(
        analysis_type="critical_habitat",
        longitude=longitude,
        latitude=latitude
    )
    
    print(f"✅ Critical Habitat Status: {habitat_result.get('status')}")
    
    # Test karst analysis
    print(f"\n🏔️ Running karst analysis")
    karst_result = await agent.run_individual_analysis(
        analysis_type="karst",
        longitude=longitude,
        latitude=latitude
    )
    
    print(f"✅ Karst Status: {karst_result.get('status')}")
    
    # Test batch analysis
    print(f"\n📍 Running batch analysis for multiple locations")
    locations = [
        {"longitude": -66.7135, "latitude": 18.4058, "name": "San_Juan"},
        {"longitude": -66.1057, "latitude": 18.4666, "name": "Bayamon"},
        {"longitude": -67.1398, "latitude": 18.2208, "name": "Mayaguez"}
    ]
    
    batch_results = await agent.batch_analysis(
        locations=locations,
        project_name="Puerto_Rico_Batch_Analysis"
    )
    
    print(f"✅ Batch Analysis: {len(batch_results)} locations processed")
    for result in batch_results:
        location_name = result.get('location', {}).get('name', 'Unknown')
        status = result.get('status', 'Unknown')
        print(f"   📍 {location_name}: {status}")
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 