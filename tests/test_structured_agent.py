#!/usr/bin/env python3
"""
Test Script for Structured Output Environmental Agent

This script tests the new structured output functionality.
"""

import os
import json
from datetime import datetime
from comprehensive_environmental_agent import create_comprehensive_environmental_agent, StructuredScreeningOutput

def test_structured_agent():
    """Test the agent with structured output"""
    print("🧪 Testing Structured Output Environmental Agent")
    print("=" * 60)
    
    # Ensure we have API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your Google API key: export GOOGLE_API_KEY='your-key-here'")
        return
    
    try:
        # Create the agent
        print("🤖 Creating comprehensive environmental agent...")
        agent = create_comprehensive_environmental_agent()
        print("✅ Agent created successfully!")
        
        # Test query
        test_query = "Environmental screening for cadastral 060-000-009-58 in Puerto Rico"
        print(f"\n📋 Test Query: {test_query}")
        print(f"🕐 Starting analysis at: {datetime.now().isoformat()}")
        
        # Run the agent
        print("\n🔄 Running environmental screening...")
        print("   This may take 3-5 minutes to complete all analyses...")
        
        response = agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config={"configurable": {"thread_id": "test_thread_123"}}
        )
        
        print("\n✅ Agent execution completed!")
        
        # Check if we have structured response
        if "structured_response" in response:
            structured_data = response["structured_response"]
            print("\n📊 STRUCTURED OUTPUT RECEIVED:")
            print("=" * 40)
            
            # Validate that it's a StructuredScreeningOutput instance
            if isinstance(structured_data, dict):
                try:
                    # Try to validate with Pydantic
                    validated_output = StructuredScreeningOutput(**structured_data)
                    print("✅ Structured output validation: PASSED")
                    
                    # Print key information
                    print(f"📁 Project Name: {validated_output.project_name}")
                    print(f"📂 Project Directory: {validated_output.project_directory}")
                    print(f"✅ Success: {validated_output.success}")
                    
                    if validated_output.property_analysis:
                        print(f"🏠 Cadastral: {validated_output.property_analysis.cadastral_number}")
                        print(f"📏 Area (acres): {validated_output.property_analysis.area_acres}")
                    
                    if validated_output.comprehensive_reports:
                        print(f"📄 JSON Report: {validated_output.comprehensive_reports.json_report}")
                        print(f"📝 Markdown Report: {validated_output.comprehensive_reports.markdown}")
                        print(f"📋 PDF Report: {validated_output.comprehensive_reports.pdf}")
                    
                    if validated_output.environmental_constraints_summary:
                        print(f"⚠️  Constraints: {len(validated_output.environmental_constraints_summary)} identified")
                    
                    print(f"📊 Risk Level: {validated_output.overall_risk_level_assessment}")
                    
                    # Save structured output to file for inspection
                    output_file = f"test_structured_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(output_file, 'w') as f:
                        json.dump(structured_data, f, indent=2, default=str)
                    print(f"\n💾 Structured output saved to: {output_file}")
                    
                except Exception as e:
                    print(f"❌ Structured output validation: FAILED - {e}")
                    print("Raw structured data:")
                    print(json.dumps(structured_data, indent=2, default=str))
            else:
                print(f"📊 Structured response type: {type(structured_data)}")
                print("Raw structured data:")
                print(structured_data)
        else:
            print("❌ No structured_response found in agent output")
            print("Available keys:", list(response.keys()))
        
        # Also show the conversational messages
        if "messages" in response:
            print(f"\n💬 Conversation Messages: {len(response['messages'])} total")
            last_message = response["messages"][-1]
            print(f"📝 Last message type: {type(last_message)}")
            if hasattr(last_message, 'content'):
                content_preview = str(last_message.content)[:200]
                print(f"📄 Content preview: {content_preview}...")
        
        return response
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_structured_agent()
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!") 