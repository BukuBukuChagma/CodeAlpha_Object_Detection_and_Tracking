# Object Detection and Tracking API Specification

## Overview
RESTful API for object detection and tracking system that supports:
- Real-time video processing via webcam
- Video file upload and processing
- Image upload and processing
- Configuration management
- Result retrieval

## Base URL
`/api/v1`

## Endpoints

### 1. Image Processing
#### Upload and Process Image
- **Endpoint**: `/detect/image`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `image`: Image file (required)
  - `conf_threshold`: float, 0-1 (optional, default=0.5)
  - `display_width`: int (optional, default=640)

- **Response**:

```json
{
"success": true,
"data": {
"detections": [
{
"bbox": [x1, y1, x2, y2],
"class_name": "string",
"confidence": float,
"track_id": int
}
],
"processed_image_url": "string",
"processing_time": float
}
}
```

### 2. Video Processing
#### Upload and Process Video
- **Endpoint**: `/detect/video`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `video`: Video file (required)
  - `conf_threshold`: float, 0-1 (optional, default=0.5)
  - `display_width`: int (optional, default=640)
  - `save_output`: boolean (optional, default=false)

- **Response**:

```json
{
"success": true,
"data": {
"task_id": "string",
"status": "processing",
"output_video_url": "string"
}
}
```

#### Get Video Processing Status
- **Endpoint**: `/detect/video/status/<task_id>`
- **Method**: GET
- **Response**:
```json
{
"success": true,
"data": {
"task_id": "string",
"status": "string", // processing/completed/failed
"progress": float, // 0-100
"output_video_url": "string",
"error": "string" // if status is failed
}
}
```

### 3. Webcam Stream
#### Start Webcam Stream
- **Endpoint**: `/stream/start`
- **Method**: POST
- **Parameters**:
  - `conf_threshold`: float, 0-1 (optional, default=0.5)
  - `display_width`: int (optional, default=640)
- **Response**:

```json
{
"success": true,
"data": {
"stream_id": "string",
"stream_url": "string" // WebSocket URL for real-time stream
}
}
```

#### Stop Webcam Stream
- **Endpoint**: `/stream/stop/<stream_id>`
- **Method**: POST
- **Response**:

```json
{
"success": true,
"data": {
"stream_id": "string",
"status": "stopped"
}
}
```

### 4. Configuration
#### Get Current Configuration
- **Endpoint**: `/config`
- **Method**: GET
- **Response**:

```json
{
"success": true,
"data": {
"model": "string",
"tracker": "string",
"conf_threshold": float,
"trajectory_length": int,
"fade_steps": int,
"display_width": int
}
}
```

#### Update Configuration
- **Endpoint**: `/config`
- **Method**: PUT
- **Body**:

```json
{
"model": "string",
"tracker": "string",
"conf_threshold": float,
"trajectory_length": int,
"fade_steps": int,
"display_width": int
}
```

- **Response**: Same as GET /config

## Error Responses
All endpoints return error responses in the following format:

```json
{
"success": false,
"error": {
"code": "string",
"message": "string",
"details": {} // Optional additional error details
}
}
```

## WebSocket Stream Format
For real-time webcam streaming, the WebSocket sends frames in the following format:

```json
{
"frame": "base64_encoded_image",
"detections": [
{
"bbox": [x1, y1, x2, y2],
"class_name": "string",
"confidence": float,
"track_id": int
}
],
"timestamp": float
}
```

## Implementation Notes
1. All file uploads have a size limit of 16MB
2. Supported image formats: JPG, PNG, BMP
3. Supported video formats: MP4, AVI, MOV
4. WebSocket stream uses JPEG compression for frames
5. All processed images/videos are stored temporarily and cleaned up after 24 hours