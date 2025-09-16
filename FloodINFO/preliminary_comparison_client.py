#!/usr/bin/env python3
"""
FEMA Preliminary Comparison Tool Client

Client for generating FEMA Preliminary Comparison reports that compare
current effective flood data with preliminary flood data.
"""

import requests
import json
import time
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PreliminaryComparisonRequest:
    """Data class for Preliminary Comparison Tool request"""
    longitude: float
    latitude: float
    location_name: Optional[str] = None


@dataclass
class PreliminaryComparisonResponse:
    """Data class for Preliminary Comparison Tool response"""
    success: bool
    job_id: Optional[str] = None
    pdf_url: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    request_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class FEMAPreliminaryComparisonClient:
    """
    Client for generating FEMA Preliminary Comparison reports using FEMA's service
    """
    
    def __init__(self):
        self.base_url = "https://msc.fema.gov/arcgis/rest/services"
        self.service_url = f"{self.base_url}/PreliminaryComparisonTool/PreliminaryComparisonToolB/GPServer/Preliminary%20Comparison%20Tool"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PreliminaryComparison-Client/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_comparison_report(self, longitude: float, latitude: float,
                                 location_name: str = None, max_retries: int = 3) -> Tuple[bool, str, str]:
        """
        Generate a Preliminary Comparison report for given coordinates
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Tuple of (success, pdf_url_or_error, job_id)
        """
        
        last_error = None
        last_job_id = None
        
        for attempt in range(max_retries):
            if attempt > 0:
                # Exponential backoff: 2, 4, 8 seconds
                wait_time = 2 ** attempt
                print(f"🔄 Retrying (attempt {attempt + 1}/{max_retries}) after {wait_time} seconds...")
                time.sleep(wait_time)
            
            try:
                result = self._attempt_comparison_generation(longitude, latitude, location_name)
                if result[0]:  # Success
                    return result
                else:
                    last_error = result[1]
                    last_job_id = result[2]
                    print(f"⚠️  Attempt {attempt + 1} failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                print(f"⚠️  Attempt {attempt + 1} encountered error: {e}")
        
        # All retries failed
        return False, f"Failed after {max_retries} attempts. Last error: {last_error}", last_job_id
    
    def _attempt_comparison_generation(self, longitude: float, latitude: float,
                                     location_name: str = None) -> Tuple[bool, str, str]:
        """
        Single attempt to generate a Preliminary Comparison report
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            
        Returns:
            Tuple of (success, pdf_url_or_error, job_id)
        """
        
        try:
            print(f"📊 Generating Preliminary Comparison report for coordinates: {latitude}, {longitude}")
            
            # Convert lat/lon to Web Mercator (EPSG:3857/102100) as used by FEMA
            def lat_lon_to_web_mercator(lat, lon):
                """Convert lat/lon to Web Mercator coordinates"""
                x = lon * 20037508.34 / 180
                y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
                y = y * 20037508.34 / 180
                return x, y
            
            x_mercator, y_mercator = lat_lon_to_web_mercator(latitude, longitude)
            
            # Create InputPoint parameter in the format FEMA expects
            input_point = {
                "geometryType": "esriGeometryPoint",
                "features": [
                    {
                        "geometry": {
                            "x": x_mercator,
                            "y": y_mercator,
                            "spatialReference": {"wkid": 102100}
                        }
                    }
                ],
                "sr": {"wkid": 102100}
            }
            
            # Submit job parameters
            submit_url = f"{self.service_url}/submitJob"
            params = {
                'f': 'json',
                'env:outSR': '102100',
                'InputPoint': json.dumps(input_point)
            }
            
            print(f"📤 Submitting job to: {submit_url}")
            print(f"📋 Parameters: {params}")
            
            # Submit the job
            response = self.session.post(submit_url, data=params, timeout=30)
            
            print(f"📨 Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"📄 Response: {json.dumps(result, indent=2)}")
                    
                    job_status = result.get('jobStatus')
                    job_id = result.get('jobId')
                    
                    if job_status == 'esriJobSubmitted' and job_id:
                        print(f"✅ Job submitted successfully. Job ID: {job_id}")
                        
                        # Poll for completion
                        pdf_url = self._poll_comparison_job(job_id)
                        
                        if pdf_url:
                            return True, pdf_url, job_id
                        else:
                            return False, "Job completed but no PDF URL found", job_id
                    
                    elif job_status == 'esriJobSucceeded':
                        # Job completed immediately - extract PDF URL
                        print(f"✅ Job completed immediately!")
                        
                        # Get the OutputFile URL
                        pdf_url = self._extract_comparison_output_url(job_id, result)
                        
                        if pdf_url:
                            print(f"📄 PDF URL extracted: {pdf_url}")
                            return True, pdf_url, job_id
                        else:
                            return False, "Job succeeded but could not extract PDF URL", job_id
                    
                    else:
                        error_msg = f"Job failed with status: {job_status}"
                        if 'messages' in result:
                            messages = [msg.get('description', '') for msg in result['messages']]
                            error_msg += f". Messages: {'; '.join(messages)}"
                        
                        return False, error_msg, job_id
                        
                except ValueError as e:
                    return False, f"Invalid JSON response: {str(e)}", None
            else:
                return False, f"HTTP {response.status_code}: {response.text[:200]}", None
                
        except Exception as e:
            return False, f"Error generating Preliminary Comparison report: {str(e)}", None
    
    def _poll_comparison_job(self, job_id: str, max_wait: int = 180, interval: int = 3) -> Optional[str]:
        """
        Poll comparison job until completion
        
        Args:
            job_id: Job ID to poll
            max_wait: Maximum wait time in seconds (default: 180)
            interval: Poll interval in seconds (default: 3)
            
        Returns:
            PDF URL if successful, None otherwise
        """
        
        job_url = f"{self.service_url}/jobs/{job_id}"
        start_time = time.time()
        
        print(f"⏳ Polling job {job_id} for completion...")
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(f"{job_url}?f=json", timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    job_status = result.get('jobStatus')
                    
                    print(f"📊 Job status: {job_status}")
                    
                    if job_status == 'esriJobSucceeded':
                        # Get the result - try different result parameter names
                        result_urls_to_try = [
                            f"{job_url}/results/OutputFile?f=json",
                            f"{job_url}/results/Output_File?f=json"
                        ]
                        
                        for result_url in result_urls_to_try:
                            print(f"🔍 Trying result URL: {result_url}")
                            result_response = self.session.get(result_url, timeout=15)
                            
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                print(f"📄 Result data: {json.dumps(result_data, indent=2)}")
                                
                                # Extract URL from different possible formats
                                pdf_url = None
                                
                                # Format: {"value": {"url": "..."}}
                                if 'value' in result_data:
                                    value = result_data['value']
                                    if isinstance(value, dict) and 'url' in value:
                                        pdf_url = value['url']
                                    elif isinstance(value, str):
                                        pdf_url = value
                                
                                if pdf_url:
                                    print(f"✅ Preliminary Comparison report generated successfully!")
                                    print(f"📄 PDF URL: {pdf_url}")
                                    return pdf_url
                            else:
                                print(f"⚠️  Failed to get result from {result_url}: HTTP {result_response.status_code}")
                        
                        # If we get here, we couldn't extract the URL from results
                        print(f"⚠️  Could not extract PDF URL from job results")
                    
                    elif job_status in ['esriJobFailed', 'esriJobCancelled', 'esriJobTimedOut']:
                        print(f"❌ Job failed with status: {job_status}")
                        
                        # Try to get error messages from the job
                        if 'messages' in result:
                            print("📋 Job error messages:")
                            for msg in result.get('messages', []):
                                msg_type = msg.get('type', 'Unknown')
                                msg_desc = msg.get('description', 'No description')
                                print(f"   - [{msg_type}] {msg_desc}")
                        
                        # Check if there's no preliminary data available
                        # This is a common reason for failure
                        messages_text = str(result.get('messages', ''))
                        if 'no preliminary' in messages_text.lower() or 'no data' in messages_text.lower():
                            print("ℹ️  No preliminary flood data available for this location")
                            print("   This means there are no proposed flood map changes for this area.")
                        
                        return None
                    
                    # Job still running, wait and try again
                    time.sleep(interval)
                else:
                    print(f"⚠️  Error polling job: HTTP {response.status_code}")
                    time.sleep(interval)
                    
            except Exception as e:
                print(f"⚠️  Error polling job: {e}")
                time.sleep(interval)
        
        print(f"⏰ Job polling timed out after {max_wait} seconds")
        return None
    
    def _extract_comparison_output_url(self, job_id: str, job_result: Dict[str, Any]) -> Optional[str]:
        """
        Extract the OutputFile URL from a completed comparison job
        
        Args:
            job_id: The job ID
            job_result: The job result JSON
            
        Returns:
            PDF URL if found, None otherwise
        """
        
        try:
            # Check if results contain OutputFile parameter URL
            results = job_result.get('results', {})
            
            if 'OutputFile' in results:
                param_url = results['OutputFile'].get('paramUrl')
                
                if param_url:
                    # Construct full URL to get the actual file URL
                    full_url = f"{self.service_url}/jobs/{job_id}/{param_url}?f=json"
                    
                    print(f"🔗 Fetching output file URL from: {full_url}")
                    
                    response = self.session.get(full_url, timeout=15)
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        
                        # Extract the actual file URL
                        # Format: {"value": {"url": "..."}}
                        file_data = result_data.get('value', {})
                        
                        if isinstance(file_data, dict) and 'url' in file_data:
                            return file_data['url']
                        elif isinstance(file_data, str):
                            return file_data
                        else:
                            print(f"⚠️  Unexpected file URL format: {file_data}")
                            return None
                    else:
                        print(f"⚠️  Failed to fetch output file URL: HTTP {response.status_code}")
                        return None
            
            print(f"⚠️  No OutputFile found in results")
            return None
            
        except Exception as e:
            print(f"⚠️  Error extracting output file URL: {e}")
            return None
    
    def download_comparison_report(self, download_url: str, filename: str = None) -> bool:
        """
        Download the Preliminary Comparison report from the provided URL
        
        Args:
            download_url: URL to download the report from
            filename: Local filename to save to (optional)
            
        Returns:
            True if download successful, False otherwise
        """
        
        if not filename:
            # Generate filename from timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"preliminary_comparison_{timestamp}.pdf"
        
        try:
            response = self.session.get(download_url, timeout=60)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"Preliminary Comparison report downloaded successfully: {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading Preliminary Comparison report: {e}")
            return False
    
    def generate_and_download_comparison(self, longitude: float, latitude: float,
                                       location_name: str = None,
                                       filename: str = None) -> Tuple[bool, str]:
        """
        Generate and download a Preliminary Comparison report in one operation
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            filename: Local filename to save to (optional)
            
        Returns:
            Tuple of (success, message)
        """
        
        print(f"Generating Preliminary Comparison report for coordinates: {latitude}, {longitude}")
        
        # Generate the report
        success, result, job_id = self.generate_comparison_report(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if not success:
            return False, f"Failed to generate Preliminary Comparison report: {result}"
        
        if not result:
            return False, "No download URL received"
        
        print(f"Preliminary Comparison report generated successfully. Job ID: {job_id}")
        print(f"Download URL: {result}")
        
        # Download the file
        if self.download_comparison_report(result, filename):
            return True, f"Preliminary Comparison report generated and downloaded successfully"
        else:
            return False, "Report generated but download failed"


def main():
    """Example usage of the Preliminary Comparison client"""
    
    client = FEMAPreliminaryComparisonClient()
    
    # Example coordinates (Cataño, Puerto Rico)
    longitude = -66.1689712
    latitude = 18.4282314
    location_name = "Cataño, Puerto Rico"
    
    print("=== FEMA Preliminary Comparison Report Example ===")
    print(f"Location: {location_name}")
    print(f"Coordinates: {latitude}, {longitude}")
    
    # Generate and download comparison report
    success, message = client.generate_and_download_comparison(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        filename="catano_preliminary_comparison.pdf"
    )
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")


if __name__ == "__main__":
    main() 