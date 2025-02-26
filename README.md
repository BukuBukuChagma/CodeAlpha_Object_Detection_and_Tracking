# Object Detection and Tracking System

## Project Overview

This project is a comprehensive object detection and tracking system that uses YOLO (You Only Look Once) to detect and track objects in images, videos, and live webcam feeds. The system provides a web interface for easy interaction and visualization of detection results.

## Web Demo

[![Web Demo Youtube Thumbnail](https://img.youtube.com/vi/34j_97WzCDw/maxresdefault.jpg)](https://www.youtube.com/watch?v=34j_97WzCDw)

## Features

- **Image Processing**: Upload and process images to detect objects
- **Video Processing**: Upload and process videos with object detection and tracking
- **Live Webcam Detection**: Real-time object detection and tracking from webcam feed
- **Adjustable Confidence Threshold**: Control detection sensitivity
- **Real-time Statistics**: View FPS and object count during processing
- **Asynchronous Processing**: Background processing for videos using Celery
- **REST API**: Programmatic access to all detection features

## Technologies Used

- **Backend**: Flask, Python, Socket.IO
- **Computer Vision**: OpenCV, YOLO (Ultralytics)
- **Machine Learning**: PyTorch
- **Async Processing**: Celery, Redis
- **Frontend**: HTML, CSS, JavaScript
- **Real-time Communication**: WebSockets

## Installation

### Prerequisites

- Python 3.8+
- Redis (Linux) or Memurai (Windows) for Celery task queue
- Webcam (for live detection)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/BukuBukuChagma/CodeAlpha_Object_Detection_and_Tracking.git
   cd CodeAlpha_Object_Detection_and_Tracking
   ```

2. Create and activate a virtual environment: (I'd installing pytorch-gpu for this project and setting up gpu and cuda for it)
   ```bash
   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Redis (Linux) or Memurai (Windows):
   
   **Linux**:
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo systemctl start redis-server
   ```
   
   **Windows**:
   - Download and install [Memurai](https://www.memurai.com/get-memurai) (Redis alternative for Windows)
   - Start Memurai from the Start menu

## Running the Application

1. Start the Redis/Memurai server (if not already running)

2. Start the Celery worker (in a separate terminal):
   ```bash
   # Linux/macOS
   celery -A src.web.tasks worker --loglevel=info
   
   # Windows
   celery -A src.web.tasks worker --loglevel=info --pool=solo
   ```

3. Start the Flask application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

5. When running for first time, YOLO model will be downloaded automatically. This may take a while depending on the model selected in script (Default is YOLOv8n).

## Usage

### Image Detection
1. Navigate to the "Image" tab
2. Upload an image
3. Adjust confidence threshold if needed
4. Click "Process Image"
5. View detection results

### Video Processing
1. Navigate to the "Video" tab
2. Upload a video file
3. Adjust confidence threshold if needed
4. Click "Process Video"
5. Wait for processing to complete
6. View and download processed video

### Live Webcam Detection
1. Navigate to the "Webcam" tab
2. Adjust confidence threshold if needed
3. Click "Start Stream"
4. View real-time detection results
5. Click "Stop Stream" when finished

## API Documentation

For detailed API documentation, please refer to the [API Documentation](docs/) in the docs directory.

## Project Structure

```
object-detection-system/
├── app.py                      # Main web application entry point
├── main.py                     # Main cli entry point
├── requirements.txt            # Project dependencies
├── docs/                       # API Documentation
├── demo_files/                 # Demo files for testing (an image, and a video)
├── src/
│   ├── detection_and_tracking/  # Detection and tracking modules
│   ├── utils/                  # Utility functions
│   └── web/                    # Web application
│       ├── static/             # Static files (CSS, JS)
│       ├── templates/          # HTML templates
│       ├── config.py           # Application configuration
│       ├── socket_handler.py   # WebSocket handlers
│       ├── utils.py            # Utility functions for web
│       └── tasks.py            # Celery tasks
└── tests/                      # Test suite
```

## Command Line Interface

In addition to the web interface, this project provides a command-line interface through `main.py` for direct access to detection and tracking functionality.

### CLI Usage

```bash
python main.py [command] [options]
```

### Available Commands

- `image`: Process a single image
- `video`: Process a video file
- `webcam`: Process live webcam feed

### Examples

#### Process an Image

```bash
python main.py image --path /path/to/image.jpg --conf 0.5
```

Options:
- `--path`: Path to the image file (required)
- `--conf`: Confidence threshold (default: 0.5)
- `--display-width`: Width of the display window (default: 1280)

#### Process a Video

```bash
python main.py video --path /path/to/video.mp4 --conf 0.4
```

Options:
- `--path`: Path to the video file (required)
- `--conf`: Confidence threshold (default: 0.5)
- `--display-width`: Width of the display window (default: 1280)

#### Start Webcam Detection

```bash
python main.py webcam --conf 0.5 --camera-id 0
```

Options:
- `--conf`: Confidence threshold (default: 0.5)
- `--camera-id`: Camera device ID (default: 1)
- `--display-width`: Width of the display window (default: 1280)

### Keyboard Controls

When using the CLI with video or webcam modes:
- Press `q` to quit the application
- Press `s` to save the current frame (in webcam mode)

## Troubleshooting

### Common Issues

1. **Webcam not working**:
   - Ensure your webcam is properly connected
   - Try changing the camera ID in `src/web/socket_handler.py` (default is 1)

2. **Redis/Celery connection issues**:
   - Verify Redis/Memurai is running
   - Check connection settings in the application

3. **YOLO model loading errors**:
   - Ensure the model weights are in the correct location
   - Check for sufficient disk space and memory

For more troubleshooting information, see [Troubleshooting Guide](docs/troubleshooting.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Ultralytics](https://github.com/ultralytics/yolov5) for the YOLO implementation
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [OpenCV](https://opencv.org/) for computer vision capabilities


