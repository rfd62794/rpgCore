"""
DGT Client - The "Body" UI Consumer
ADR 123: Local-First Microservice Bridge - Truth Consumer

The Client consumes simulation state and renders it through different display modes.
It can connect to local or remote simulation servers.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, Union
from queue import Queue, Empty
from enum import Enum
import json
import socket
from pathlib import Path
import sys

# Add parent directories for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger
from .engines.body import BodyEngine, DisplayMode, TRI_MODAL_AVAILABLE

class ConnectionState(Enum):
    """Connection states to simulation server"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

@dataclass
class ClientConfig:
    """Configuration for UI client"""
    display_mode: DisplayMode = DisplayMode.TERMINAL
    update_rate_hz: int = 30
    max_queue_size: int = 10
    connection_timeout: float = 5.0
    heartbeat_interval: float = 1.0
    auto_reconnect: bool = True
    local_mode: bool = True  # Local queue vs remote socket

class LocalClient:
    """Local client using shared memory queue"""
    
    def __init__(self, state_queue: Queue):
        self.state_queue = state_queue
        self.connection_state = ConnectionState.CONNECTED
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get latest state from local queue"""
        try:
            # Non-blocking get
            return self.state_queue.get_nowait()
        except Empty:
            # No new state available
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.connection_state == ConnectionState.CONNECTED

class RemoteClient:
    """Remote client using socket connection"""
    
    def __init__(self, host: str = "localhost", port: int = 5555):
        self.host = host
        self.port = port
        self.socket = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.buffer = ""
    
    def connect(self) -> bool:
        """Connect to remote simulation server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connection_state = ConnectionState.CONNECTED
            logger.info(f"🔗 Connected to remote server {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to remote server: {e}")
            self.connection_state = ConnectionState.ERROR
            return False
    
    def disconnect(self):
        """Disconnect from remote server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connection_state = ConnectionState.DISCONNECTED
        logger.info("🔌 Disconnected from remote server")
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get state from remote server"""
        if not self.is_connected():
            return None
        
        try:
            # Send request for state
            request = json.dumps({"type": "get_state"}).encode() + b'\n'
            self.socket.send(request)
            
            # Receive response
            response = self.socket.recv(4096).decode()
            if response:
                return json.loads(response)
            
        except Exception as e:
            logger.error(f"❌ Failed to get remote state: {e}")
            self.connection_state = ConnectionState.ERROR
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.connection_state == ConnectionState.CONNECTED and self.socket is not None

class UIClient:
    """
    The "Body" - Truth Consumer
    
    Consumes simulation state and renders it through display modes.
    Implements ADR 123: Local-First Microservice Bridge
    """
    
    def __init__(self, config: Optional[ClientConfig] = None):
        self.config = config or ClientConfig()
        self.running = False
        self.frame_count = 0
        
        # Display engine
        self.display_engine: Optional[BodyEngine] = None
        if TRI_MODAL_AVAILABLE:
            self.display_engine = BodyEngine(
                use_tri_modal=True, 
                universal_packet_enforcement=True
            )
        
        # Client connection
        self.client: Optional[Union[LocalClient, RemoteClient]] = None
        
        # Performance tracking
        self.last_frame_time = time.time()
        self.fps_history = []
        self.max_fps_history = 60
        
        # Threading
        self.render_thread: Optional[threading.Thread] = None
        
        # State tracking
        self.last_state: Optional[Dict[str, Any]] = None
        self.state_queue = Queue(maxsize=self.config.max_queue_size)
        
        logger.info("🎭 DGT UI Client initialized")
    
    def connect_to_local_server(self, state_queue: Queue) -> bool:
        """Connect to local simulation server"""
        try:
            self.client = LocalClient(state_queue)
            logger.info("🔗 Connected to local simulation server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to local server: {e}")
            return False
    
    def connect_to_remote_server(self, host: str = "localhost", port: int = 5555) -> bool:
        """Connect to remote simulation server"""
        try:
            self.client = RemoteClient(host, port)
            success = self.client.connect()
            if success:
                logger.info(f"🌐 Connected to remote server {host}:{port}")
            return success
        except Exception as e:
            logger.error(f"❌ Failed to connect to remote server: {e}")
            return False
    
    def start(self) -> bool:
        """Start the UI client"""
        if self.running:
            logger.warning("⚠️ UI client already running")
            return False
        
        if not self.display_engine:
            logger.error("❌ Display engine not available")
            return False
        
        if not self.client:
            logger.error("❌ No server connection")
            return False
        
        # Set display mode
        if not self.display_engine.set_mode(self.config.display_mode):
            logger.error(f"❌ Failed to set display mode: {self.config.display_mode}")
            return False
        
        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()
        
        logger.info(f"🎮 UI Client started in {self.config.display_mode.value} mode")
        return True
    
    def stop(self):
        """Stop the UI client"""
        if not self.running:
            return
        
        self.running = False
        
        if self.render_thread and self.render_thread.is_alive():
            self.render_thread.join(timeout=1.0)
        
        logger.info("🛑 UI Client stopped")
    
    def _render_loop(self):
        """Main render loop"""
        logger.info("🔄 Render loop started")
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Get state from server
            state = self._get_server_state()
            
            if state:
                # Render state
                self._render_state(state)
                self.last_state = state
                self.frame_count += 1
            
            # Update performance tracking
            self._update_performance_stats(dt)
            
            # Frame rate limiting
            target_dt = 1.0 / self.config.update_rate_hz
            sleep_time = max(0, target_dt - dt)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("🔄 Render loop ended")
    
    def _get_server_state(self) -> Optional[Dict[str, Any]]:
        """Get state from server"""
        if not self.client or not self.client.is_connected():
            return None
        
        try:
            state = self.client.get_state()
            if state:
                # Add to local queue for reference
                try:
                    self.state_queue.put_nowait(state)
                except:
                    # Queue full, drop oldest
                    try:
                        self.state_queue.get_nowait()
                        self.state_queue.put_nowait(state)
                    except:
                        pass
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Failed to get server state: {e}")
            return None
    
    def _render_state(self, state: Dict[str, Any]):
        """Render state using display engine"""
        try:
            if self.display_engine:
                success = self.display_engine.render(state, self.config.display_mode)
                
                if not success:
                    logger.warning("⚠️ Render failed")
        
        except Exception as e:
            logger.error(f"❌ Render error: {e}")
    
    def _update_performance_stats(self, dt: float):
        """Update performance statistics"""
        self.fps_history.append(dt)
        if len(self.fps_history) > self.max_fps_history:
            self.fps_history.pop(0)
    
    def _get_current_fps(self) -> float:
        """Get current FPS"""
        if self.fps_history:
            avg_dt = sum(self.fps_history) / len(self.fps_history)
            return 1.0 / avg_dt if avg_dt > 0 else 0
        return 0
    
    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get latest received state"""
        try:
            return self.state_queue.get_nowait()
        except Empty:
            return self.last_state
    
    def switch_mode(self, mode: DisplayMode) -> bool:
        """Switch display mode"""
        if not self.display_engine:
            return False
        
        success = self.display_engine.set_mode(mode)
        if success:
            self.config.display_mode = mode
            logger.info(f"🎭 Switched to {mode.value} mode")
        
        return success
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get client performance statistics"""
        stats = {
            'client_type': 'ui_client',
            'running': self.running,
            'frame_count': self.frame_count,
            'current_fps': self._get_current_fps(),
            'target_fps': self.config.update_rate_hz,
            'display_mode': self.config.display_mode.value if self.config.display_mode else None,
            'connection_state': self.client.connection_state.value if self.client else None,
            'queue_size': self.state_queue.qsize(),
            'last_state_time': self.last_state.get('timestamp') if self.last_state else None
        }
        
        # Add display engine stats
        if self.display_engine:
            display_stats = self.display_engine.update_performance_stats()
            stats['display_engine'] = display_stats
        
        return stats
    
    def cleanup(self):
        """Cleanup client resources"""
        self.stop()
        
        if self.display_engine:
            self.display_engine.cleanup()
        
        if self.client and hasattr(self.client, 'disconnect'):
            self.client.disconnect()
        
        self.state_queue = None
        logger.info("🧹 UI Client cleaned up")

# Factory functions
def create_local_client(state_queue: Queue, mode: DisplayMode = DisplayMode.TERMINAL) -> UIClient:
    """Create local UI client"""
    config = ClientConfig(display_mode=mode, local_mode=True)
    client = UIClient(config)
    client.connect_to_local_server(state_queue)
    return client

def create_remote_client(host: str = "localhost", port: int = 5555, 
                        mode: DisplayMode = DisplayMode.TERMINAL) -> UIClient:
    """Create remote UI client"""
    config = ClientConfig(display_mode=mode, local_mode=False)
    client = UIClient(config)
    client.connect_to_remote_server(host, port)
    return client

# Standalone client runner
def run_standalone_client(mode: str = "terminal"):
    """Run UI client in standalone mode"""
    import signal
    import sys
    
    try:
        display_mode = DisplayMode[mode.upper()]
    except KeyError:
        print(f"❌ Invalid mode: {mode}. Use terminal, cockpit, or ppu")
        return
    
    # Create a mock state queue for demo
    from queue import Queue
    mock_queue = Queue()
    
    # Create client
    client = create_local_client(mock_queue, display_mode)
    
    def signal_handler(sig, frame):
        print("\n🛑 Stopping UI client...")
        client.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"🎭 DGT UI Client - Standalone Mode ({mode})")
    print("=" * 50)
    print("Waiting for simulation state...")
    print("Press Ctrl+C to stop")
    print()
    
    # Start client
    if not client.start():
        print("❌ Failed to start UI client")
        return
    
    # Mock simulation data for demo
    def mock_simulation():
        counter = 0
        while client.running:
            # Create mock state
            state = {
                'frame_count': counter,
                'timestamp': time.time(),
                'entities': [
                    {'id': 'player', 'x': 10 + (counter % 5), 'y': 10 + (counter % 3), 'type': 'dynamic'},
                    {'id': 'npc', 'x': 15, 'y': 15, 'type': 'dynamic'},
                ],
                'background': {'id': 'demo_bg'},
                'hud': {
                    'line_1': f'Demo Mode: {mode.title()}',
                    'line_2': f'Frame: {counter}',
                    'line_3': f'Time: {time.strftime("%H:%M:%S")}',
                    'line_4': 'Mock Simulation Data'
                }
            }
            
            # Add to queue
            try:
                mock_queue.put(state)
            except:
                pass  # Queue full
            
            counter += 1
            time.sleep(1.0 / 30)  # 30 Hz simulation
    
    # Start mock simulation
    import threading
    sim_thread = threading.Thread(target=mock_simulation, daemon=True)
    sim_thread.start()
    
    try:
        # Keep client running
        while client.running:
            time.sleep(1)
            
            # Print stats every 10 seconds
            if client.frame_count % 300 == 0:
                stats = client.get_performance_stats()
                print(f"📊 Client Stats: FPS: {stats['current_fps']:.1f}, Frames: {stats['frame_count']}")
    
    except KeyboardInterrupt:
        pass
    finally:
        client.cleanup()
        print("✅ UI Client stopped")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "terminal"
    run_standalone_client(mode)
