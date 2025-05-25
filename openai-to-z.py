# OpenAI to Z Challenge - Archaeological Site Discovery Pipeline
# This script integrates GPT-4.1 text analysis and Sentinel-2 anomaly detection

import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from shapely.geometry import box
from urllib.request import urlretrieve

# --- CONFIGURATION ---

from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or "sk-YOUR_API"  # Use environment variable for safety
)
TEXT_INPUT_FILE = "gpt_prompts/historical_excerpt.txt"
SENTINEL_IMAGE_PATH = "data/sentinel_sample.tif"
OUTPUT_HYPOTHESIS = "reports/final_hypothesis.md"

# Sample Sentinel image fallback - updated to an example valid URL for a single band
SENTINEL_SAMPLE_URL = "https://sentinel-s2-l1c.s3.amazonaws.com/tiles/10/T/ET/2022/6/1/0/B08.jp2"

# --- GPT-4.1 ANALYSIS ---
def extract_archaeological_clues():
    if not os.path.exists(TEXT_INPUT_FILE):
        raise FileNotFoundError(f"Missing historical text file: {TEXT_INPUT_FILE}")

    with open(TEXT_INPUT_FILE, "r", encoding="utf-8") as f:
        document = f.read()

    prompt = f"""
You are an expert in archaeology and natural language inference.

Task: Analyze the following text to extract any hints about ancient or indigenous settlements, ruins, unusual earthworks, or unexplored human activity within the Amazon region.

Instructions:
1. Identify place names, directions, and distances.
2. Correlate landscape features (rivers, plateaus, forest clearings) with possible human activity.
3. Use reasoning to infer if a region may hide an archaeological site.
4. Output coordinates if mentioned or suggest an approximate region.

Text:
{document}
"""

    try:
        completion = client.chat.completions.create(
              model="gpt-4o-mini",
              store=True,
              messages=[
                {"role": "user", "content": prompt}
              ]
            )
        response = completion.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        response = "⚠️ GPT analysis failed or quota exceeded."

    os.makedirs(os.path.dirname(OUTPUT_HYPOTHESIS), exist_ok=True)
    with open(OUTPUT_HYPOTHESIS, "w", encoding="utf-8") as f:
        f.write("# Final Hypothesis\n\n")
        f.write(response)

    print("✅ GPT-4.1 analysis complete. Hypothesis written to report.")

# --- SENTINEL IMAGE VISUALIZATION ---
def download_sample_image_if_missing():
    if not os.path.exists(SENTINEL_IMAGE_PATH):
        os.makedirs(os.path.dirname(SENTINEL_IMAGE_PATH), exist_ok=True)
        print(f"⚠️ {SENTINEL_IMAGE_PATH} not found. Downloading sample image...")
        try:
            urlretrieve(SENTINEL_SAMPLE_URL, SENTINEL_IMAGE_PATH)
            print("✅ Sample Sentinel image downloaded.")
        except Exception as e:
            print(f"❌ Failed to download sample Sentinel image: {e}")

def visualize_sentinel_image():
    download_sample_image_if_missing()

    try:
        with rasterio.open(SENTINEL_IMAGE_PATH) as src:
            print(f"📦 Loaded Sentinel-2 image: {SENTINEL_IMAGE_PATH}")
            print(f"📊 Bands available: {src.count}")
            for i in range(1, src.count + 1):
                print(f" - Band {i} dtype: {src.dtypes[i-1]}")

            fig, ax = plt.subplots(1, figsize=(12, 10))

            # Check if band 8 is available before trying to show it
            if src.count >= 8:
                show((src, 8), ax=ax, title="Sentinel-2: Band 8 (NIR) - Vegetation Anomaly Detection")
            else:
                # If no band 8, just show the first band available
                show(src.read(1), ax=ax, title=f"Sentinel-2: Band 1 (only band available)")
                print(f"⚠️ Sentinel image has only {src.count} band(s). Showing first band instead.")

            os.makedirs("reports", exist_ok=True)
            plt.savefig("reports/sentinel_band8.png")
            print("📷 NIR band image saved to reports/sentinel_band8.png")

    except Exception as e:
        print(f"❌ Error loading or visualizing Sentinel image: {e}")

# --- PIPELINE RUNNER ---
if __name__ == "__main__":
    extract_archaeological_clues()
    visualize_sentinel_image()
