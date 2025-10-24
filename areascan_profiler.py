#!/usr/bin/env python3
"""
AreaScan Profiler - CLI Tool
Test inference models on production machines (similar to ops-counter CLI)
"""
import time
import click
from pathlib import Path
from PIL import Image
import numpy as np
from clients.inference_client import InferenceClient


print("=" * 70)
print("  AREASCAN PROFILER - COMMAND LINE INTERFACE")
print("=" * 70)
print("Connecting to installed AreaScanInference service...")


@click.command()
@click.option('--image', type=click.Path(exists=True), help='Path to image file')
@click.option('--folder', type=click.Path(exists=True), help='Path to folder with images')
@click.option('--model', type=click.Choice(['detection', 'segmentation', 'both']), 
              default='both', help='Which model to run')
@click.option('--port', type=int, default=None, help='AreaScanInference service port')
@click.option('--confidence', type=float, default=0.5, help='Confidence threshold (0.0-1.0)')
@click.option('--host', type=str, default='localhost', help='Service host')
def main(image: str, folder: str, model: str, port: int, confidence: float, host: str):
    """AreaScan Profiler - Test inference models on prod machines"""
    
    # Initialize client (like ops-counter initializes SessionInfoClient)
    try:
        client = InferenceClient(port=port, host=host)
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return 1
    
    # Check service health
    print("Checking service health...")
    if not client.check_health():
        print("✗ AreaScanInference service is not available")
        print("  Make sure the service is running and accessible")
        return 1
    
    print(f"✓ Service is healthy on {client.address}")
    print()
    
    # Get image paths
    if image:
        image_paths = [Path(image)]
    elif folder:
        folder_path = Path(folder)
        image_paths = list(folder_path.glob('*.jpg')) + \
                     list(folder_path.glob('*.png')) + \
                     list(folder_path.glob('*.jpeg')) + \
                     list(folder_path.glob('*.bmp'))
    else:
        print("✗ Please provide --image or --folder")
        return 1
    
    if not image_paths:
        print("✗ No images found")
        return 1
    
    print(f"Processing {len(image_paths)} image(s)...")
    print(f"Confidence threshold: {confidence:.0%}")
    print()
    
    # Process each image
    total_detection_time = 0
    total_segmentation_time = 0
    
    for idx, img_path in enumerate(image_paths, 1):
        print(f"{'=' * 70}")
        print(f"[{idx}/{len(image_paths)}] Image: {img_path.name}")
        print(f"{'=' * 70}")
        
        try:
            # Load and resize image
            print(f"Loading image...")
            img = Image.open(img_path)
            original_size = img.size
            print(f"  Original size: {original_size[0]}x{original_size[1]}")
            
            # Resize to standard size
            target_size = (2560, 2048)
            img_resized = img.resize(target_size)
            img_array = np.array(img_resized)
            
            # Convert to bytes (RGB format)
            if img_array.ndim == 2:  # Grayscale
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]
            
            image_bytes = img_array.tobytes()
            print(f"  Resized to: {target_size[0]}x{target_size[1]}")
            
            # Run object detection
            if model in ['detection', 'both']:
                print(f"\n[Object Detection Model]")
                print(f"  Running inference...")
                start = time.time()
                result = client.detect_objects(
                    image_bytes, 
                    target_size[0], 
                    target_size[1],
                    confidence_threshold=confidence
                )
                duration = (time.time() - start) * 1000
                total_detection_time += duration
                
                print(f"  ✓ Found: {result['prediction_count']} objects")
                print(f"  ✓ Latency: {duration:.2f} ms")
                
                if result['predictions']:
                    print(f"  Top predictions:")
                    for i, pred in enumerate(result['predictions'][:5], 1):  # Show top 5
                        print(f"    {i}. {pred['class']:<15} "
                              f"confidence: {pred['confidence']:.2%}  "
                              f"center: ({pred['center_x']:.0f}, {pred['center_y']:.0f})  "
                              f"size: {pred['width']:.0f}x{pred['height']:.0f}")
            
            # Run sheet segmentation
            if model in ['segmentation', 'both']:
                print(f"\n[Sheet Segmentation Model]")
                print(f"  Running inference...")
                start = time.time()
                result = client.segment_sheets(
                    image_bytes, 
                    target_size[0], 
                    target_size[1],
                    confidence_threshold=confidence
                )
                duration = (time.time() - start) * 1000
                total_segmentation_time += duration
                
                print(f"  ✓ Found: {result['prediction_count']} segments")
                print(f"  ✓ Latency: {duration:.2f} ms")
                
                if result['predictions']:
                    print(f"  Top predictions:")
                    for i, pred in enumerate(result['predictions'][:5], 1):  # Show top 5
                        print(f"    {i}. {pred['class']:<15} "
                              f"confidence: {pred['confidence']:.2%}  "
                              f"center: ({pred['center_x']:.0f}, {pred['center_y']:.0f})  "
                              f"polygon points: {len(pred.get('polygon_points', []))}")
            
            print()
            
        except Exception as e:
            print(f"✗ Error processing image: {e}")
            continue
    
    # Summary
    print(f"{'=' * 70}")
    print(f"  PROFILING SUMMARY")
    print(f"{'=' * 70}")
    print(f"Images processed: {len(image_paths)}")
    if model in ['detection', 'both'] and total_detection_time > 0:
        avg_detection = total_detection_time / len(image_paths)
        print(f"Average detection latency: {avg_detection:.2f} ms")
    if model in ['segmentation', 'both'] and total_segmentation_time > 0:
        avg_segmentation = total_segmentation_time / len(image_paths)
        print(f"Average segmentation latency: {avg_segmentation:.2f} ms")
    print(f"{'=' * 70}")
    
    client.close()
    print("\n✓ Profiling complete")
    return 0


if __name__ == "__main__":
    exit(main())