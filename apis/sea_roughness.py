from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import numpy as np
import os
from datetime import datetime
from dotenv import load_dotenv
from sentinelhub import SHConfig, SentinelHubRequest, MimeType, CRS, BBox, DataCollection, SentinelHubCatalog

app = FastAPI()
load_dotenv()

CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")

class GeoBounds(BaseModel):
    west: float
    south: float
    east: float
    north: float

@app.post("/average-sea-roughness")
async def average_sea_roughness(
    bbox: GeoBounds,
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    width: int = Query(512, description="Output image width"),
    height: int = Query(512, description="Output image height")
):
    # Create fresh config and inject token
    config = SHConfig()
    config.sh_client_id = CLIENT_ID
    config.sh_client_secret = CLIENT_SECRET
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"

    bounding_box = BBox([bbox.west, bbox.south, bbox.east, bbox.north], CRS.WGS84)

    # Check if data is available using the catalog (simplified)
    try:
        catalog = SentinelHubCatalog(config=config)
        
        search_iterator = catalog.search(
            DataCollection.SENTINEL1_IW.define_from("s1grd", service_url=config.sh_base_url),
            bbox=bounding_box,
            time=(start_date, end_date),
        )
        
        results = list(search_iterator)
        print(f"Found {len(results)} Sentinel-1 tiles in the specified area and time range")
        
        if len(results) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No Sentinel-1 data available for the specified area and time range. Try a longer time period or different location."
            )
            
        # Print some details about available data
        for i, tile in enumerate(results[:3]):  # Show first 3
            print(f"Tile {i}: {tile.get('properties', {})}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Catalog search warning: {str(e)}")
        # Continue anyway, the actual request might still work

    # Fixed evalscript with proper handling of temporal data
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["VV"],
                units: "LINEAR_POWER"
            }],
            output: {
                bands: 1,
                sampleType: "FLOAT32"
            },
            mosaicking: "ORBIT"
        };
    }

    function evaluatePixel(samples) {
        // Check if we have any samples
        if (!samples || samples.length === 0) {
            return [NaN];
        }
        
        // Calculate mean across all available observations
        let sum = 0;
        let count = 0;
        
        for (let i = 0; i < samples.length; i++) {
            if (samples[i] && samples[i].VV !== null && !isNaN(samples[i].VV)) {
                sum += samples[i].VV;
                count++;
            }
        }
        
        return count > 0 ? [sum / count] : [NaN];
    }
    """
    
    try:
        req = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL1_IW.define_from(
                        "s1grd",
                        service_url=config.sh_base_url
                    ),
                    time_interval=(start_date, end_date),
                )
            ],
            responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
            bbox=bounding_box,
            size=(width, height),
            config=config
        )

        print("Requesting data from Sentinel Hub...")
        data = req.get_data()
        
        if not data or len(data) == 0:
            raise HTTPException(status_code=500, detail="No data returned from Sentinel Hub")
        
        print(f"Data shape: {data[0].shape if data else 'No data'}")
        print(f"Data min/max: {np.nanmin(data[0]) if data else 'N/A'}/{np.nanmax(data[0]) if data else 'N/A'}")
        print(f"NaN count: {np.sum(np.isnan(data[0])) if data else 'N/A'}")
        
        # Extract VV band
        vv_band = data[0][:, :, 0] if data[0].ndim == 3 else data[0]
        
        # Filter valid pixels (just exclude NaN)
        valid_pixels = vv_band[~np.isnan(vv_band)]
        
        if valid_pixels.size == 0:
            raise HTTPException(
                status_code=404, 
                detail="No valid VV backscatter data found. Try a different date range or location."
            )
        
        average_roughness = float(np.mean(valid_pixels))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

    return {
        "bounding_box": [bbox.west, bbox.south, bbox.east, bbox.north],
        "time_range": {"start": start_date, "end": end_date},
        "average_sea_roughness_vv": average_roughness,
        "valid_pixels_count": int(valid_pixels.size)
    }