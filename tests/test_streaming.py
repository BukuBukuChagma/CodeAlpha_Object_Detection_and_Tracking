import pytest
from flask_socketio import SocketIOTestClient
import time
import json
import base64
from src.web.app import app, socketio
from src.web.socket_handler import active_streams
import threading
import eventlet
import socket
import logging
import traceback

eventlet.monkey_patch()

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(port, timeout=10):
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.1)
    return False

@pytest.fixture(scope="session", autouse=True)
def setup_test_server():
    """Setup test server before running tests."""
    # Configure app for testing
    app.config['TESTING'] = True
    
    def run_server():
        try:
            socketio.run(app, 
                        host='127.0.0.1',
                        port=5001,
                        use_reloader=False,
                        debug=True,
                        allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"Server error: {e}")
            raise
    
    # Start server in thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    yield
    
    # No need to explicitly stop the server as it's a daemon thread

@pytest.fixture
def socket_client():
    """Create a Socket.IO test client."""
    client = None
    try:
        # Create client with explicit connection parameters
        client = SocketIOTestClient(
            app, 
            socketio,
            namespace='/stream'  # Simplify the connection parameters
        )
        yield client
    finally:
        if client:
            try:
                client.disconnect(namespace='/stream')
            except:
                pass

@pytest.fixture
def http_client():
    """Create a Flask test client."""
    with app.test_client() as client:
        yield client

def test_stream_start(http_client):
    """Test starting a stream."""
    response = http_client.post('/api/v1/stream/start', data={
        'conf_threshold': '0.5'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'stream_id' in data['data']
    assert 'stream_url' in data['data']
    assert data['data']['stream_url'].startswith('ws://')
    
    # Cleanup
    stream_id = data['data']['stream_id']
    if stream_id in active_streams:
        active_streams[stream_id].stop()
        del active_streams[stream_id]

def test_stream_stop_invalid_id(http_client):
    """Test stopping a non-existent stream."""
    response = http_client.post('/api/v1/stream/stop/invalid_id')
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'stream_error'
    assert 'not found' in data['error']['message'].lower()

def test_stream_with_invalid_parameters(http_client):
    """Test stream start with invalid parameters."""
    response = http_client.post('/api/v1/stream/start', data={
        'conf_threshold': 'invalid'
    })
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['error']['code'] == 'stream_error'

def test_multiple_streams(http_client):
    """Test handling multiple streams."""
    streams = []
    try:
        # Start multiple streams
        for _ in range(3):
            response = http_client.post('/api/v1/stream/start', data={
                'conf_threshold': '0.5'
            })
            assert response.status_code == 200
            stream_id = response.get_json()['data']['stream_id']
            streams.append(stream_id)
            
        # Verify all streams are active
        for stream_id in streams:
            assert stream_id in active_streams
            
    finally:
        # Cleanup
        for stream_id in streams:
            if stream_id in active_streams:
                response = http_client.post(f'/api/v1/stream/stop/{stream_id}')
                assert response.status_code == 200

def wait_for_socket_event(socket_client, event_name, timeout=5):
    """Wait for a specific socket event."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        for event in socket_client.get_received('/stream'):
            if event['name'] == event_name:
                return event
        time.sleep(0.1)
    return None

def test_stream_flow(http_client, socket_client):
    """Test complete streaming flow with WebSocket."""
    stream_id = None
    try:
        # Start stream
        response = http_client.post('/api/v1/stream/start', data={
            'conf_threshold': '0.5'
        })
        assert response.status_code == 200
        stream_id = response.get_json()['data']['stream_id']
        
        # Connect socket with better error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\nAttempting WebSocket connection (attempt {attempt + 1})")
                
                # Try to establish connection
                socket_client.connect(namespace='/stream')
                time.sleep(0.5)  # Wait for connection to establish
                
                # Check for connect event
                events = socket_client.get_received('/stream')
                print(f"Received events: {[event['name'] for event in events]}")
                
                if any(event['name'] == 'connect' for event in events):
                    print("Received connect event")
                    break
                print("No connect event received")
            except Exception as e:
                print(f"Connection error: {str(e)}")
                traceback.print_exc()
            time.sleep(1)
            
        # Verify connection by checking for connect event
        assert any(event['name'] == 'connect' for event in events), "No connect event received"
        
        # Wait for frames with more detailed logging
        frames_received = 0
        start_time = time.time()
        while time.time() - start_time < 5 and frames_received < 3:
            frame_event = wait_for_socket_event(socket_client, 'frame', timeout=1)
            if frame_event:
                frames_received += 1
                data = frame_event['args'][0]
                
                # Verify frame data structure
                assert 'stream_id' in data
                assert 'frame' in data
                assert 'detections' in data
                assert 'timestamp' in data
                
                # Verify frame is valid base64 without printing it
                try:
                    frame_bytes = base64.b64decode(data['frame'])
                    assert len(frame_bytes) > 0
                except Exception as e:
                    assert False, f"Invalid base64 frame data: {str(e)}"
        
        assert frames_received > 0, "No frames received"
        
    finally:
        try:
            # Cleanup
            if stream_id in active_streams:
                active_streams[stream_id].stop()
                del active_streams[stream_id]
        except:
            pass

def test_get_detections(http_client, socket_client):
    """Test getting detections from stream."""
    stream_id = None
    try:
        # Start stream
        response = http_client.post('/api/v1/stream/start', data={
            'conf_threshold': '0.5'
        })
        assert response.status_code == 200
        stream_id = response.get_json()['data']['stream_id']
        
        # Connect socket
        socket_client.connect(namespace='/stream')
        
        # Wait for connection
        events = socket_client.get_received('/stream')
        assert any(event['name'] == 'connect' for event in events)
        
        # Request detections
        socket_client.emit('get_detections', {'stream_id': stream_id}, namespace='/stream')
        
        # Wait for response
        events = socket_client.get_received('/stream')
        assert any(event['name'] == 'detections' for event in events)
        
        # Verify detection data
        detection_event = next(e for e in events if e['name'] == 'detections')
        data = detection_event['args'][0]
        assert 'stream_id' in data
        assert 'detections' in data
        assert 'timestamp' in data
        assert data['stream_id'] == stream_id
        
    finally:
        if stream_id in active_streams:
            active_streams[stream_id].stop()
            del active_streams[stream_id]

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up any remaining streams after each test."""
    yield
    # Clean up any remaining streams
    for stream_id in list(active_streams.keys()):
        try:
            stream = active_streams[stream_id]
            stream.stop()
            del active_streams[stream_id]
        except Exception as e:
            print(f"Error during cleanup: {e}") 