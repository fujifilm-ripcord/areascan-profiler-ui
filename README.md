# AreaScan Profiler

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-green.svg)
![gRPC](https://img.shields.io/badge/gRPC-1.63.0-orange.svg)
![License](https://img.shields.io/badge/license-Internal-red.svg)

**Independent Python tool for profiling AreaScan inference models on production machines**

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Contributing](#contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI Mode](#gui-mode)
  - [CLI Mode](#cli-mode)
- [Configuration](#configuration)
- [Adding New Models](#adding-new-models)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Related Projects](#related-projects)

---

## 🎯 Overview

**AreaScan Profiler** is a standalone Python application designed for testing and profiling machine learning inference models used in the FBRC pipeline. Similar to the [ops-counter](https://github.com/fujifilm-ripcord/ops-counter) tool, it operates independently of the main `rip-workcell` application while communicating with the AreaScanInference service via gRPC.

### Why AreaScan Profiler?

- **🔬 Production Testing**: Test inference models directly on production machines without disrupting workflows
- **📊 Performance Metrics**: Measure latency, throughput, and accuracy of ML models
- **🎨 Dual Interface**: Use GUI for interactive testing or CLI for automated batch processing
- **🔌 Independent Operation**: No dependency on ScanApp or rip-workcell runtime
- **📈 Real-time Feedback**: Instant visualization of detection results and confidence scores

---

## ✨ Features

### Current Capabilities

- **🎯 Object Detection**: Profile object detection models (staples, labels, barcodes)
- **📄 Sheet Segmentation**: Test sheet segmentation and polygon detection
- **🖼️ Image Processing**: Support for JPG, PNG, BMP formats with automatic resizing
- **⚡ Performance Metrics**: Measure inference latency with microsecond precision
- **🎛️ Adjustable Thresholds**: Real-time confidence, overlap, and opacity controls
- **📁 Batch Processing**: Process single images or entire folders
- **🎨 Modern UI**: Clean, responsive PyQt6 interface with drag-and-drop support
- **📋 Detailed Logging**: Comprehensive prediction results with formatted output

### Supported Models

| Model | Description | Status |
|-------|-------------|--------|
| **Object Detection** | Detect and classify objects (staples, labels, etc.) | ✅ Active |
| **Sheet Segmentation** | Segment and extract sheet boundaries | ✅ Active |
| **Blank Page Classification** | *Coming Soon* | 🔜 Planned |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 AreaScan Profiler (Python)                  │
│  ┌──────────────────┐              ┌───────────────────┐   │
│  │   GUI (PyQt6)    │              │   CLI (Click)     │   │
│  │                  │              │                   │   │
│  │  - Drag & Drop   │              │  - Batch Process  │   │
│  │  - Live Preview  │              │  - Automation     │   │
│  │  - Adjustable    │              │  - Scripting      │   │
│  └────────┬─────────┘              └─────────┬─────────┘   │
│           │                                   │             │
│           └───────────┬───────────────────────┘             │
│                       │                                     │
│           ┌───────────▼─────────────┐                       │
│           │  InferenceClient        │                       │
│           │  (gRPC Client)          │                       │
│           └───────────┬─────────────┘                       │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ gRPC (Port 60021)
                        │
            ┌───────────▼──────────────┐
            │  AreaScanInference       │
            │  Service (rip-workcell)  │
            │                          │
            │  - Object Detection      │
            │  - Sheet Segmentation    │
            │  - Model Management      │
            └──────────────────────────┘
```

### Key Components

- **GUI Layer**: PyQt6-based interactive interface with real-time preview
- **CLI Layer**: Click-based command-line tool for automation
- **gRPC Client**: Handles communication with AreaScanInference service
- **Image Processing**: PIL/Pillow for image manipulation and preprocessing
- **Configuration**: Auto-detection of service ports from workcell settings

---

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows 10/11 (for production deployment)
- **AreaScanInference Service**: Must be running and accessible
- **Network**: Access to localhost:60021 (or configured port)

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4 GB | 8 GB |
| Disk Space | 500 MB | 1 GB |
| Python | 3.8 | 3.10+ |

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fujifilm-ripcord/areascan-profiler-ui.git
cd areascan-profiler-ui
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Obtain Proto Files

Copy the required `.proto` files from the rip-workcell repository:

```bash
# Create proto directory
mkdir proto

# Copy proto files (adjust paths as needed)
copy C:\path\to\rip-workcell\Workcell.Contracts\Protos\AreaScanInference\AreaScanInferenceService.proto proto\area_scan_inference.proto
copy C:\path\to\rip-workcell\Workcell.Contracts\Protos\ripcord_grpc.proto proto\ripcord_grpc.proto
```

### 5. Generate gRPC Stubs

```bash
python generate_grpc.py
```

**Expected Output:**
```
Found 2 .proto files:
  - area_scan_inference.proto
  - ripcord_grpc.proto

Generating Python stubs...
  Generating area_scan_inference.proto...
  Generating ripcord_grpc.proto...

Fixing imports in generated files...
  ✓ Fixed imports in area_scan_inference_pb2.py
  ✓ Fixed imports in area_scan_inference_pb2_grpc.py

✓ Successfully generated gRPC stubs
```

### 6. Verify Installation

```bash
# Check CLI
python areascan_profiler.py --help

# Launch GUI
python areascan_profiler_ui.py
```

---

## 🎮 Usage

### GUI Mode

Launch the graphical interface for interactive testing:

```bash
python areascan_profiler_ui.py
```

#### GUI Features

1. **Upload Section** (Left Panel)
   - Drag & drop images or folders
   - Browse files button
   - Path input for direct entry
   - Model selection dropdown

2. **Image Preview** (Center)
   - Live image display
   - Maintains aspect ratio
   - Dark background for clarity

3. **Controls Panel** (Right)
   - Confidence threshold slider (0-100%)
   - Overlap threshold slider
   - Opacity threshold slider
   - Run inference button
   - Real-time predictions display

#### Workflow Example

```
1. Select Image → 2. Choose Model → 3. Adjust Thresholds → 4. Run Inference → 5. View Results
```

### CLI Mode

Use the command-line interface for batch processing and automation:

#### Basic Commands

```bash
# Profile a single image
python areascan_profiler.py --image path/to/image.jpg

# Profile a folder of images
python areascan_profiler.py --folder path/to/images/

# Specify model type
python areascan_profiler.py --image test.jpg --model detection

# Adjust confidence threshold
python areascan_profiler.py --image test.jpg --confidence 0.7

# Custom service port
python areascan_profiler.py --image test.jpg --port 60021
```

#### CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--image` | PATH | - | Path to single image file |
| `--folder` | PATH | - | Path to folder with images |
| `--model` | CHOICE | `both` | Model to run: `detection`, `segmentation`, `both` |
| `--port` | INT | Auto | AreaScanInference service port |
| `--confidence` | FLOAT | `0.5` | Confidence threshold (0.0-1.0) |
| `--host` | TEXT | `localhost` | Service host address |

#### Example Output

```
======================================================================
  AREASCAN PROFILER - COMMAND LINE INTERFACE
======================================================================
✓ Connected to AreaScanInference service on localhost:60021
✓ Service is healthy on localhost:60021

Processing 1 image(s)...
Confidence threshold: 50%

======================================================================
[1/1] Image: document_001.jpg
======================================================================
Loading image...
  Original size: 2560x2048
  Resized to: 2560x2048

[Object Detection Model]
  Running inference...
  ✓ Found: 12 objects
  ✓ Latency: 245.32 ms
  Top predictions:
    1. staple          confidence: 95.23%  center: (1280, 1024)
    2. label           confidence: 89.45%  center: (1400, 900)

[Sheet Segmentation Model]
  Running inference...
  ✓ Found: 3 segments
  ✓ Latency: 312.45 ms

======================================================================
  PROFILING SUMMARY
======================================================================
Images processed: 1
Average detection latency: 245.32 ms
Average segmentation latency: 312.45 ms
======================================================================
```

---

## ⚙️ Configuration

### Auto-Configuration

The profiler automatically reads service configuration from:

```
C:\Ripcord\settings\workcell_base.json
C:\Ripcord\settings\workcell.json
```

**Expected JSON Structure:**
```json
{
  "ApplicationGrpcSettings": {
    "GrpcServices": {
      "AreaScanInference": {
        "ServerPort": 60021
      }
    }
  }
}
```

### Manual Configuration

Override automatic configuration with command-line arguments:

```bash
python areascan_profiler.py --image test.jpg --port 60021 --host localhost
```

---

## 🔧 Adding New Models

The profiler is designed to easily accommodate new inference models. Follow these steps to integrate a new model:

### Step 1: Update Proto Definition

Edit `proto/area_scan_inference.proto` to add your new service method:

```protobuf
service AreaScanInference {
    // Existing methods
    rpc DetectObjects(DetectObjectsRequest) returns (DetectObjectsResponse);
    rpc SegmentSheets(SegmentSheetsRequest) returns (SegmentSheetsResponse);
    
    // 🆕 NEW: Your new model
    rpc ClassifyDocuments(ClassifyDocumentsRequest) returns (ClassifyDocumentsResponse);
}

// 🆕 NEW: Define request/response messages
message ClassifyDocumentsRequest {
    string id = 1;
    bytes image_bytes = 2;
    int32 channels = 3;
    int32 image_height = 4;
    int32 image_width = 5;
}

message ClassifyDocumentsResponse {
    repeated DocumentClassification predictions = 1;
}

message DocumentClassification {
    string document_type = 1;
    float confidence = 2;
}
```

### Step 2: Regenerate gRPC Stubs

```bash
python generate_grpc.py
```

### Step 3: Add Client Method

In `clients/inference_client.py`, add a new method:

```python
def classify_documents(self, image_bytes: bytes, width: int, height: int,
                      confidence_threshold: float = 0.0) -> Dict[str, Any]:
    """Classify documents in image."""
    try:
        request = area_scan_inference_pb2.ClassifyDocumentsRequest(
            id=str(uuid.uuid4()),
            image_bytes=image_bytes,
            image_height=height,
            image_width=width,
            channels=3
        )
        
        response = self.stub.ClassifyDocuments(request, timeout=30.0)
        
        predictions = [
            {
                'document_type': pred.document_type,
                'confidence': pred.confidence,
            }
            for pred in response.predictions
            if pred.confidence >= confidence_threshold
        ]
        
        return {
            'prediction_count': len(predictions),
            'predictions': predictions
        }
    except grpc.RpcError as e:
        raise Exception(f"Document classification failed: {e.code()}")
```

### Step 4: Update CLI

In `areascan_profiler.py`:

**A. Add to model choices:**
```python
@click.option('--model', type=click.Choice(['detection', 'segmentation', 'classification', 'all']), 
              default='all', help='Which model to run')
```

**B. Add processing logic:**
```python
if model in ['classification', 'all']:
    result = client.classify_documents(image_bytes, width, height, confidence)
    # Display results
```

### Step 5: Update GUI

In `areascan_profiler_ui.py`:

**A. Update dropdown:**
```python
self.model_combo.addItems([
    'Object Detection',
    'Sheet Segmentation',
    'Document Classification',  # NEW
    'All Models'
])
```

**B. Update worker and display logic** to handle the new model type.

### Step 6: Test

```bash
# Test CLI
python areascan_profiler.py --image test.jpg --model classification

# Test GUI
python areascan_profiler_ui.py
# Select "Document Classification" from dropdown
```

---

## 👨‍💻 Development

### Project Structure

```
areascan-profiler-ui/
├── clients/                      # gRPC client implementations
│   ├── __init__.py
│   └── inference_client.py      # Main inference client
├── generated/                    # Auto-generated gRPC stubs
│   ├── __init__.py
│   ├── area_scan_inference_pb2.py
│   ├── area_scan_inference_pb2_grpc.py
│   ├── ripcord_grpc_pb2.py
│   └── ripcord_grpc_pb2_grpc.py
├── proto/                        # Protocol buffer definitions
│   ├── area_scan_inference.proto
│   └── ripcord_grpc.proto
├── areascan_profiler.py         # CLI application
├── areascan_profiler_ui.py      # GUI application
├── generate_grpc.py             # Stub generator script
├── requirements.txt             # Python dependencies
├── setup.py                     # Package configuration
└── README.md                    # This file
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black pylint mypy

# Format code
black .

# Lint code
pylint areascan_profiler.py areascan_profiler_ui.py clients/

# Type check
mypy areascan_profiler.py
```

### Running Tests

```bash
# Run unit tests (when available)
pytest tests/

# Test gRPC connection
python -c "from clients.inference_client import InferenceClient; c = InferenceClient(); print(c.check_health())"
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "No module named 'generated'"

**Solution:**
```bash
python generate_grpc.py
```

#### Issue: "Service not available"

**Causes:**
- AreaScanInference service not running
- Incorrect port configuration
- Firewall blocking connection

**Solution:**
```bash
# Check service status
# Verify port in C:\Ripcord\settings\workcell_base.json
# Try manual port specification
python areascan_profiler.py --image test.jpg --port 60021
```

#### Issue: "Import error: cannot import area_scan_inference_pb2"

**Solution:**
```bash
# Clean generated files
del generated\*.py

# Ensure proto files exist
dir proto\*.proto

# Regenerate
python generate_grpc.py
```

#### Issue: GUI not displaying correctly

**Solution:**
```bash
# Reinstall PyQt6
pip uninstall PyQt6
pip install PyQt6==6.7.0
```

### Debug Mode

Enable verbose logging:

```python
# In inference_client.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
   ```bash
   git commit -m "feat: add document classification model"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions
- Keep functions focused and small
- Write meaningful variable names

---

## 📚 Related Projects

- **[rip-workcell](https://github.com/MoffettData/rip-workcell)** - Main workcell application
- **[ops-counter](https://github.com/fujifilm-ripcord/ops-counter)** - Operator counting tool (similar architecture)
---

## 📄 License

Internal FBRC tool - Not for external distribution

---

## 🙏 Acknowledgments

- Inspired by [ops-counter](https://github.com/fujifilm-ripcord/ops-counter) architecture
- Built for the  Dev  team
- Thanks to the rip-workcell team for the gRPC infrastructure

---

## 📞 Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/your-org/areascan-profiler-ui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/areascan-profiler-ui/discussions)
- **Slack**: #FBRC (Internal)

---

<div align="center">

**Made with ❤️ by the FBRC Dev Team**

[⬆ Back to Top](#areascan-profiler)

</div>
