import pytest
import io
import os
from pathlib import Path
import cv2
import numpy as np
from app import app
from src.web.utils import FileHandler
import time

@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_image():
    """Create a test image."""
    # Create a simple test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (30, 30), (70, 70), (0, 255, 0), -1)
    
    # Save to bytes
    is_success, buffer = cv2.imencode(".jpg", img)
    if not is_success:
        raise ValueError("Could not create test image")
    
    return io.BytesIO(buffer.tobytes())

@pytest.fixture
def test_video():
    """Get path to demo video file."""
    video_path = Path(__file__).parent.parent / 'demo_files/demo_video.mp4'
    if not video_path.exists():
        raise FileNotFoundError(f"Demo video not found at {video_path}")
    
    # Read video file into memory for testing
    with open(video_path, 'rb') as f:
        video_data = f.read()
    return io.BytesIO(video_data)

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'healthy'

def test_process_image_no_file(client):
    """Test image processing endpoint with no file."""
    response = client.post('/api/v1/detect/image')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'missing_file'

def test_process_image_empty_filename(client):
    """Test image processing endpoint with empty filename."""
    response = client.post('/api/v1/detect/image', data={
        'image': (io.BytesIO(), '')
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'invalid_file'

def test_process_image_invalid_type(client):
    """Test image processing endpoint with invalid file type."""
    response = client.post('/api/v1/detect/image', data={
        'image': (io.BytesIO(b'test'), 'test.txt')
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'invalid_file_type'

def test_process_image_success(client, test_image):
    """Test successful image processing."""
    response = client.post('/api/v1/detect/image', data={
        'image': (test_image, 'test.jpg'),
        'conf_threshold': '0.5',
        'display_width': '640'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'detections' in data['data']
    assert 'processed_image_url' in data['data']
    assert 'processing_time' in data['data']
    
    # Update path check for new static location
    result_path = Path('src/web') / data['data']['processed_image_url'].lstrip('/')
    assert result_path.exists()

def test_process_image_with_parameters(client, test_image):
    """Test image processing with different parameters."""
    response = client.post('/api/v1/detect/image', data={
        'image': (test_image, 'test.jpg'),
        'conf_threshold': '0.8',
        'display_width': '800'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_process_video_no_file(client):
    """Test video processing endpoint with no file."""
    response = client.post('/api/v1/detect/video')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'missing_file'

def test_process_video_empty_filename(client):
    """Test video processing endpoint with empty filename."""
    response = client.post('/api/v1/detect/video', data={
        'video': (io.BytesIO(), '')
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'invalid_file'

def test_process_video_invalid_type(client):
    """Test video processing endpoint with invalid file type."""
    response = client.post('/api/v1/detect/video', data={
        'video': (io.BytesIO(b'test'), 'test.txt')
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'invalid_file_type'

def test_video_status_invalid_id(client):
    """Test video status endpoint with invalid task ID."""
    response = client.get('/api/v1/detect/video/status/invalid_task_id')
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'status_error'
    assert 'message' in data['error']

def test_video_processing_flow(client, test_video):
    """Test complete video processing flow."""
    # Start processing
    response = client.post('/api/v1/detect/video', data={
        'video': (test_video, 'demo_video.mp4'),
        'conf_threshold': '0.5',
        'display_width': '640',
        'save_output': 'true'
    })
    assert response.status_code == 200
    task_id = response.get_json()['data']['task_id']

    # Small delay to ensure file is written
    time.sleep(1)

    # Check initial status
    response = client.get(f'/api/v1/detect/video/status/{task_id}')
    assert response.status_code == 200
    
    # Wait for processing to complete (with timeout)
    timeout = time.time() + 20  # 20 second timeout
    while time.time() < timeout:
        response = client.get(f'/api/v1/detect/video/status/{task_id}')
        data = response.get_json()
        if data['data']['status'] in ['completed', 'failed']:
            break
        time.sleep(1)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['status'] in ['completed', 'failed']

def test_process_video_with_parameters(client, test_video):
    """Test video processing with different parameters."""
    response = client.post('/api/v1/detect/video', data={
        'video': (test_video, 'demo_video.mp4'),
        'conf_threshold': '0.8',
        'display_width': '800',
        'save_output': 'false'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'task_id' in data['data']

def test_get_config(client):
    """Test getting current configuration."""
    response = client.get('/api/v1/config')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Verify config structure
    config = data['data']
    assert 'model' in config
    assert 'tracker' in config
    assert 'conf_threshold' in config
    assert 'trajectory_length' in config
    assert 'fade_steps' in config
    assert 'display_width' in config
    
    # Verify data types
    assert isinstance(config['conf_threshold'], float)
    assert isinstance(config['trajectory_length'], int)
    assert isinstance(config['fade_steps'], int)
    assert isinstance(config['display_width'], int)

def test_update_config_no_data(client):
    """Test updating config with no data."""
    response = client.put('/api/v1/config')
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'config_error'

def test_update_config_invalid_data(client):
    """Test updating config with invalid data."""
    response = client.put('/api/v1/config', json={
        'conf_threshold': 'invalid',
        'trajectory_length': 'invalid'
    })
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'config_error'

def test_update_config_success(client):
    """Test successful config update."""
    # Get original config
    original = client.get('/api/v1/config').get_json()['data']
    
    # Update config
    new_config = {
        'conf_threshold': 0.7,
        'trajectory_length': 20,
        'fade_steps': 5
    }
    response = client.put('/api/v1/config', json=new_config)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Verify updates
    config = data['data']
    for key, value in new_config.items():
        assert config[key] == value
    
    # Verify unchanged values
    assert config['model'] == original['model']
    assert config['tracker'] == original['tracker']
    assert config['display_width'] == original['display_width']

def test_update_config_partial(client):
    """Test partial config update."""
    # Update only one setting
    response = client.put('/api/v1/config', json={
        'conf_threshold': 0.8
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['conf_threshold'] == 0.8

def test_update_config_bounds(client):
    """Test config value bounds."""
    # Test invalid values
    invalid_configs = [
        {'conf_threshold': 2.0},  # Above 1.0
        {'conf_threshold': -1.0},  # Below 0.0
        {'trajectory_length': -5},  # Negative
        {'fade_steps': -1}  # Negative
    ]
    
    for config in invalid_configs:
        response = client.put('/api/v1/config', json=config)
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'config_error'

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test files after each test."""
    yield
    # Update cleanup paths
    upload_dir = Path('src/web/static/uploads')
    results_dir = Path('src/web/static/results')
    
    def safe_remove(path):
        try:
            if path.exists():
                path.unlink()
        except PermissionError:
            # Wait and try again if file is locked
            import time
            time.sleep(0.1)
            try:
                path.unlink()
            except:
                pass

    if upload_dir.exists():
        for file in upload_dir.glob('*'):
            safe_remove(file)
    
    if results_dir.exists():
        for file in results_dir.glob('*'):
            safe_remove(file) 