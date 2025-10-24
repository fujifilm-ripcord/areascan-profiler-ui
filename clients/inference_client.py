import grpc
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

# Import with SINGLE underscores (as shown in your dir output)
from generated import area_scan_inference_pb2
from generated import area_scan_inference_pb2_grpc
from generated import ripcord_grpc_pb2


class InferenceClient:
    """Client for AreaScanInference service - mirrors ops-counter's SessionInfoClient pattern"""
    
    def __init__(self, port: Optional[int] = None, host: str = "localhost"):
        """
        Initialize the inference client.
        
        Args:
            port: Service port. If None, reads from workcell config
            host: Service host (default: localhost)
        """
        # Read port from workcell config (like ops-counter reads station config)
        if port is None:
            port = self._get_port_from_config()
        
        self.port = port
        self.host = host
        self.address = f"{host}:{port}"
        
        # Create insecure channel (same as ops-counter)
        self.channel = grpc.insecure_channel(
            self.address,
            options=[
                ('grpc.max_receive_message_length', 52428800),  # 50MB
                ('grpc.max_send_message_length', 52428800),     # 50MB
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
            ]
        )
        
        self.stub = area_scan_inference_pb2_grpc.AreaScanInferenceStub(self.channel)
        print(f"✓ Connected to AreaScanInference service on {self.address}")
    
    def _get_port_from_config(self) -> int:
        """
        Read port from workcell config (like ops-counter does).
        Falls back to default if config not found.
        """
        config_paths = [
            Path(r"C:\Ripcord\settings\workcell_base.json"),
            Path(r"C:\Ripcord\settings\workcell.json"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        port = config.get('ApplicationGrpcSettings', {}) \
                                    .get('GrpcServices', {}) \
                                    .get('AreaScanInference', {}) \
                                    .get('ServerPort')
                        if port:
                            print(f"✓ Read port {port} from {config_path}")
                            return port
                except Exception as e:
                    print(f"⚠ Failed to read config from {config_path}: {e}")
        
        # Fallback default
        print("⚠ Using default port 60021")
        return 60021
    
    def check_health(self) -> bool:
        """
        Health check to verify service is running.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            request = ripcord_grpc_pb2.HealthCheckRequest()
            response = self.stub.Check(request, timeout=5.0)
            return response.status == ripcord_grpc_pb2.HealthCheckResponse.SERVING
        except grpc.RpcError as e:
            print(f"✗ Health check failed: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def detect_objects(self, image_bytes: bytes, width: int, height: int, 
                      confidence_threshold: float = 0.0) -> Dict[str, Any]:
        """
        Detect objects in image.
        
        Args:
            image_bytes: Raw image bytes (RGB format)
            width: Image width
            height: Image height
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            Dictionary with prediction_count and predictions list
        """
        try:
            request = area_scan_inference_pb2.DetectObjectsRequest(
                id=str(uuid.uuid4()),
                image_bytes=image_bytes,
                image_height=height,
                image_width=width,
                channels=3
            )
            
            response = self.stub.DetectObjects(request, timeout=30.0)
            
            # Filter by confidence threshold
            predictions = [
                {
                    'class': pred.prediction_class,
                    'confidence': pred.confidence,
                    'center_x': pred.center_x,
                    'center_y': pred.center_y,
                    'width': pred.width,
                    'height': pred.height
                }
                for pred in response.predictions
                if pred.confidence >= confidence_threshold
            ]
            
            return {
                'prediction_count': len(predictions),
                'predictions': predictions
            }
            
        except grpc.RpcError as e:
            raise Exception(f"Object detection failed: {e.code()} - {e.details()}")
    
    def segment_sheets(self, image_bytes: bytes, width: int, height: int,
                      confidence_threshold: float = 0.0) -> Dict[str, Any]:
        """
        Segment sheets in image.
        
        Args:
            image_bytes: Raw image bytes (RGB format)
            width: Image width
            height: Image height
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            Dictionary with prediction_count and predictions list
        """
        try:
            request = area_scan_inference_pb2.SegmentSheetsRequest(
                id=str(uuid.uuid4()),
                image_bytes=image_bytes,
                image_height=height,
                image_width=width,
                channels=3
            )
            
            response = self.stub.SegmentSheets(request, timeout=30.0)
            
            # Filter by confidence threshold
            predictions = [
                {
                    'class': pred.prediction_class,
                    'confidence': pred.confidence,
                    'center_x': pred.center_x,
                    'center_y': pred.center_y,
                    'width': pred.width,
                    'height': pred.height,
                    'polygon_points': [(pt.x, pt.y) for pt in pred.polygon_points]
                }
                for pred in response.predictions
                if pred.confidence >= confidence_threshold
            ]
            
            return {
                'prediction_count': len(predictions),
                'predictions': predictions
            }
            
        except grpc.RpcError as e:
            raise Exception(f"Sheet segmentation failed: {e.code()} - {e.details()}")
    
    def close(self):
        """Close the gRPC channel"""
        if self.channel:
            self.channel.close()
            print("✓ Closed connection")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()