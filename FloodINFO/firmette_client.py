#!/usr/bin/env python3
"""
FEMA FIRMette Client

Client for generating FEMA FIRMette (Flood Insurance Rate Map) reports
using FEMA's Map Service Center.
"""

import requests
import json
import time
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FIRMetteRequest:
    """Data class for FIRMette request"""
    longitude: float
    latitude: float
    location_name: Optional[str] = None
    print_type: str = "FIRMETTE"  # "FIRMETTE" or "Full FIRM"
    graphic_format: str = "PDF"   # "PDF" or "PNG"


@dataclass
class FIRMetteResponse:
    """Data class for FIRMette response"""
    success: bool
    job_id: Optional[str] = None
    pdf_url: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    request_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None


class FEMAFIRMetteClient:
    """
    Client for generating FEMA FIRMette reports using FEMA's Map Service Center
    """
    
    def __init__(self):
        self.base_url = "https://msc.fema.gov/arcgis/rest/services"
        self.print_service_url = f"{self.base_url}/NFHL_Print/AGOLPrintB/GPServer/Print%20FIRM%20or%20FIRMette"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FIRMette-Client/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_firmette_via_msc(self, longitude: float, latitude: float,
                                 location_name: str = None) -> Tuple[bool, str, str]:
        """
        Generate a FIRMette using FEMA's Map Service Center
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            
        Returns:
            Tuple of (success, pdf_url_or_error, job_id)
        """
        
        try:
            print(f"🗺️  Generating FIRMette for coordinates: {latitude}, {longitude}")
            
            # Convert lat/lon to Web Mercator (EPSG:3857/102100) as used by FEMA
            def lat_lon_to_web_mercator(lat, lon):
                """Convert lat/lon to Web Mercator coordinates"""
                x = lon * 20037508.34 / 180
                y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
                y = y * 20037508.34 / 180
                return x, y
            
            x_mercator, y_mercator = lat_lon_to_web_mercator(latitude, longitude)
            
            # Create feature class with point geometry as required by FEMA service
            feature_class = {
                "displayFieldName": "",
                "geometryType": "esriGeometryPoint",
                "spatialReference": {"wkid": 102100, "latestWkid": 3857},
                "fields": [
                    {"name": "OBJECTID", "type": "esriFieldTypeOID", "alias": "OBJECTID"},
                    {"name": "myField", "type": "esriFieldTypeString", "alias": "myField", "length": 255}
                ],
                "features": [
                    {
                        "attributes": {"OBJECTID": 1, "myField": location_name or "Query Point"},
                        "geometry": {
                            "x": x_mercator,
                            "y": y_mercator,
                            "spatialReference": {"wkid": 102100}
                        }
                    }
                ],
                "exceededTransferLimit": False
            }
            
            # Submit job parameters
            submit_url = f"{self.print_service_url}/submitJob"
            params = {
                'f': 'json',
                'env:outSR': '102100',
                'FC': json.dumps(feature_class),
                'Print_Type': 'FIRMETTE',
                'graphic': 'PDF'
            }
            
            print(f"📤 Submitting FIRMette job to: {submit_url}")
            
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
                        print(f"✅ FIRMette job submitted successfully. Job ID: {job_id}")
                        
                        # Poll for completion
                        pdf_url = self._poll_firmette_job(job_id)
                        
                        if pdf_url:
                            return True, pdf_url, job_id
                        else:
                            return False, "Job completed but no PDF URL found", job_id
                    
                    elif job_status == 'esriJobSucceeded':
                        # Job completed immediately - extract PDF URL
                        print(f"✅ FIRMette job completed immediately!")
                        
                        # Get the OutputFile URL
                        pdf_url = self._extract_firmette_output_url(job_id, result)
                        
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
            return False, f"Error generating FIRMette: {str(e)}", None
    
    def _poll_firmette_job(self, job_id: str, max_wait: int = 120, interval: int = 3) -> Optional[str]:
        """
        Poll FIRMette job until completion
        
        Args:
            job_id: Job ID to poll
            max_wait: Maximum wait time in seconds
            interval: Poll interval in seconds
            
        Returns:
            PDF URL if successful, None otherwise
        """
        
        job_url = f"{self.print_service_url}/jobs/{job_id}"
        start_time = time.time()
        
        print(f"⏳ Polling FIRMette job {job_id} for completion...")
        
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
                            f"{job_url}/results/Output_File?f=json",
                            f"{job_url}/results/OutputMap?f=json"
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
                                    print(f"✅ FIRMette generated successfully!")
                                    print(f"📄 PDF URL: {pdf_url}")
                                    return pdf_url
                            else:
                                print(f"⚠️  Failed to get result from {result_url}: HTTP {result_response.status_code}")
                        
                        # If we get here, we couldn't extract the URL from results
                        print(f"⚠️  Could not extract PDF URL from job results")
                    
                    elif job_status in ['esriJobFailed', 'esriJobCancelled', 'esriJobTimedOut']:
                        print(f"❌ Job failed with status: {job_status}")
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
    
    def _extract_firmette_output_url(self, job_id: str, job_result: Dict[str, Any]) -> Optional[str]:
        """
        Extract the OutputFile URL from a completed FIRMette job
        
        Args:
            job_id: The job ID
            job_result: The job result JSON
            
        Returns:
            PDF URL if found, None otherwise
        """
        
        try:
            # Check if results contain OutputFile parameter URL
            results = job_result.get('results', {})
            
            output_params = ['OutputFile', 'Output_File', 'OutputMap']
            
            for param_name in output_params:
                if param_name in results:
                    param_url = results[param_name].get('paramUrl')
                    
                    if param_url:
                        # Construct full URL to get the actual file URL
                        full_url = f"{self.print_service_url}/jobs/{job_id}/{param_url}?f=json"
                        
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
                                continue
                        else:
                            print(f"⚠️  Failed to fetch output file URL: HTTP {response.status_code}")
                            continue
            
            print(f"⚠️  No output file found in results")
            return None
            
        except Exception as e:
            print(f"⚠️  Error extracting output file URL: {e}")
            return None
    
    def download_firmette(self, download_url: str, filename: str = None) -> bool:
        """
        Download the FIRMette from the provided URL
        
        Args:
            download_url: URL to download the FIRMette from
            filename: Local filename to save to (optional)
            
        Returns:
            True if download successful, False otherwise
        """
        
        if not filename:
            # Generate filename from timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firmette_{timestamp}.pdf"
        
        try:
            response = self.session.get(download_url, timeout=60)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"FIRMette downloaded successfully: {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading FIRMette: {e}")
            return False
    
    def generate_and_download_firmette(self, longitude: float, latitude: float,
                                     location_name: str = None,
                                     filename: str = None) -> Tuple[bool, str]:
        """
        Generate and download a FIRMette in one operation
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            filename: Local filename to save to (optional)
            
        Returns:
            Tuple of (success, message)
        """
        
        print(f"Generating FIRMette for coordinates: {latitude}, {longitude}")
        
        # Generate the FIRMette
        success, result, job_id = self.generate_firmette_via_msc(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if not success:
            return False, f"Failed to generate FIRMette: {result}"
        
        if not result:
            return False, "No download URL received"
        
        print(f"FIRMette generated successfully. Job ID: {job_id}")
        print(f"Download URL: {result}")
        
        # Download the file
        if self.download_firmette(result, filename):
            return True, f"FIRMette generated and downloaded successfully"
        else:
            return False, "FIRMette generated but download failed"


def main():
    """Example usage of the FIRMette client"""
    
    client = FEMAFIRMetteClient()
    
    # Example coordinates (Cataño, Puerto Rico)
    longitude = -66.1689712
    latitude = 18.4282314
    location_name = "Cataño, Puerto Rico"
    
    print("=== FEMA FIRMette Generation Example ===")
    print(f"Location: {location_name}")
    print(f"Coordinates: {latitude}, {longitude}")
    
    # Generate and download FIRMette
    success, message = client.generate_and_download_firmette(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        filename="catano_firmette.pdf"
    )
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")


if __name__ == "__main__":
    main() 