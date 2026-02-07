"""
Core Heartbeat - 60 FPS Async Loop

The central nervous system of the DGT Autonomous Movie System.
Manages the main game loop, frame timing, and coordination between all services.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger

from .state import GameState, VoyagerState, TARGET_FPS, FRAME_DELAY_MS
from .constants import get_system_config


@dataclass
class HeartbeatMetrics:
    """Heartbeat performance metrics"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    total_frames: int = 0
    total_time: float = 0.0
    last_frame_time: float = 0.0


class HeartbeatController:
    """60 FPS asynchronous heartbeat controller"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.metrics = HeartbeatMetrics()
        
        # Frame timing
        self.last_frame_time = 0.0
        self.frame_accumulator = 0.0
        self.target_frame_time = FRAME_DELAY_MS / 1000.0
        
        # Service references (to be injected)
        self.world_engine = None
        self.dd_engine = None
        self.voyager = None
        self.graphics_engine = None
        self.chronicler = None
        self.persistence_manager = None
        
        # Async coordination
        self.loop_task: Optional[asyncio.Task] = None
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("🫀 Heartbeat Controller initialized")
    
    def register_services(self, world_engine, dd_engine, voyager, graphics_engine, chronicler, persistence_manager):
        """Register all service dependencies"""
        self.world_engine = world_engine
        self.dd_engine = dd_engine
        self.voyager = voyager
        self.graphics_engine = graphics_engine
        self.chronicler = chronicler
        self.persistence_manager = persistence_manager
        
        logger.info("🫀 All services registered with Heartbeat")
    
    async def start(self) -> None:
        """Start the heartbeat loop"""
        if self.running:
            logger.warning("Heartbeat already running")
            return
        
        self.running = True
        self.paused = False
        self.metrics = HeartbeatMetrics()
        self.last_frame_time = time.time()
        
        # Start background tasks
        await self._start_background_tasks()
        
        # Start main heartbeat loop
        self.loop_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("🫀 Heartbeat started - 60 FPS target")
    
    async def stop(self) -> None:
        """Stop the heartbeat loop"""
        self.running = False
        
        # Cancel main loop
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.background_tasks.clear()
        
        logger.info("🫀 Heartbeat stopped")
    
    async def pause(self) -> None:
        """Pause the heartbeat (maintains rendering but stops game logic)"""
        self.paused = True
        logger.info("🫀 Heartbeat paused")
    
    async def resume(self) -> None:
        """Resume the heartbeat"""
        self.paused = False
        logger.info("🫀 Heartbeat resumed")
    
    async def _heartbeat_loop(self) -> None:
        """Main 60 FPS heartbeat loop"""
        logger.info("🫀 Starting 60 FPS heartbeat loop")
        
        while self.running:
            frame_start_time = time.time()
            
            try:
                # Execute single frame
                await self._execute_frame()
                
                # Update metrics
                await self._update_metrics(frame_start_time)
                
                # Frame rate limiting
                await self._frame_rate_limit(frame_start_time)
                
            except asyncio.CancelledError:
                logger.info("🫀 Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"💥 Heartbeat frame error: {e}")
                # Continue running despite frame errors
        
        logger.info("🫀 Heartbeat loop ended")
    
    async def _execute_frame(self) -> None:
        """Execute a single frame"""
        current_time = time.time()
        
        # Get current game state
        current_state = self.dd_engine.get_current_state()
        
        # Handle Voyager state machine
        await self._handle_voyager_state(current_state)
        
        # Process pending intents
        await self._process_pending_intents(current_state)
        
        # Update all systems
        await self._update_systems(current_state)
        
        # Render frame
        await self._render_frame(current_state)
        
        # Handle persistence
        await self._handle_persistence(current_state)
        
        # Update frame count
        current_state.frame_count += 1
    
    async def _handle_voyager_state(self, state: GameState) -> None:
        """Handle Voyager state machine logic"""
        if state.voyager_state == VoyagerState.STATE_IDLE:
            # Generate next intent from movie script or autonomous behavior
            intent = await self.voyager.generate_next_intent(state)
            if intent:
                await self.dd_engine.submit_intent(intent)
        
        elif state.voyager_state == VoyagerState.STATE_PONDERING:
            # Voyager is waiting for LLM response
            # Check if LLM has responded
            if self.chronicler.has_pending_response():
                response = await self.chronicler.get_pending_response()
                await self._handle_llm_response(response, state)
        
        elif state.voyager_state == VoyagerState.STATE_MOVING:
            # Movement in progress - check completion
            if await self.voyager.is_movement_complete():
                new_state = VoyagerState.STATE_IDLE
                await self.dd_engine.update_voyager_state(new_state)
    
    async def _process_pending_intents(self, state: GameState) -> None:
        """Process any pending intents in the D&D Engine"""
        # This is handled by the D&D Engine internally
        # Just ensure it gets processing time
        await self.dd_engine.process_queue()
    
    async def _update_systems(self, state: GameState) -> None:
        """Update all system components"""
        # Update effects and triggers
        await self.dd_engine.update_effects()
        
        # Update Voyager position if moving
        if state.voyager_state == VoyagerState.STATE_MOVING:
            await self.voyager.update_position(state.player_position)
        
        # Check for new discoveries (Interest Points)
        await self._check_discoveries(state)
        
        # Update subtitles (if chronicler is available)
        if self.chronicler:
            await self.chronicler.update_subtitles(state)
    
    async def _check_discoveries(self, state: GameState) -> None:
        """Check for new Interest Point discoveries"""
        player_pos = state.player_position
        
        # Check if player discovered an interest point
        for interest_point in state.interest_points:
            if not interest_point.discovered:
                distance = abs(player_pos[0] - interest_point.position[0]) + \
                          abs(player_pos[1] - interest_point.position[1])
                
                if distance <= 2:  # Discovery radius
                    # Mark as discovered
                    interest_point.discovered = True
                    
                    # Trigger LLM pondering
                    await self._trigger_pondering(interest_point, state)
    
    async def _trigger_pondering(self, interest_point, state: GameState) -> None:
        """Trigger LLM pondering for Interest Point"""
        # Change Voyager state to pondering
        await self.dd_engine.update_voyager_state(VoyagerState.STATE_PONDERING)
        
        # Submit ponder intent to Chronicler (if available)
        if self.chronicler:
            ponder_intent = self.chronicler.create_ponder_intent(interest_point, state)
            await self.chronicler.submit_ponder_query(ponder_intent)
        else:
            # Fallback: just log the pondering
            logger.info(f"🤔 Voyager pondering Interest Point at {interest_point.position} (Chronicler not available)")
        
        logger.info(f"🤔 Voyager pondering Interest Point at {interest_point.position}")
    
    async def _handle_llm_response(self, response: Dict[str, Any], state: GameState) -> None:
        """Handle LLM response to pondering"""
        # Extract manifestation from response
        manifestation = response.get("manifestation", "Mysterious landmark")
        
        # Find the corresponding interest point
        for interest_point in state.interest_points:
            if interest_point.discovered and not interest_point.manifestation:
                interest_point.manifestation = manifestation
                interest_point.manifestation_timestamp = time.time()
                
                # Create world delta for persistence (if manager is available)
                if self.persistence_manager:
                    delta = self.persistence_manager.create_interest_delta(interest_point)
                    await self.dd_engine.apply_world_delta(delta)
                
                # Generate subtitle (if chronicler is available)
                if self.chronicler:
                    subtitle = f"Discovered: {manifestation}"
                    await self.chronicler.add_subtitle(subtitle, 4.0)
                
                logger.info(f"✨ Interest Point manifested: {manifestation}")
                break
        
        # Return Voyager to idle state
        await self.dd_engine.update_voyager_state(VoyagerState.STATE_IDLE)
    
    async def _render_frame(self, state: GameState) -> None:
        """Render the current frame"""
        # Render game state (if graphics engine is available)
        if self.graphics_engine:
            frame = await self.graphics_engine.render_state(state)
            
            # Render subtitles (if chronicler is available)
            if self.chronicler:
                subtitles = await self.chronicler.get_current_subtitles()
                await self.graphics_engine.render_subtitles(frame, subtitles)
            
            # Display frame
            await self.graphics_engine.display_frame(frame)
    
    async def _handle_persistence(self, state: GameState) -> None:
        """Handle persistence operations"""
        # Check if persistence is needed and manager is available
        if self.persistence_manager and state.turn_count % 10 == 0:  # Every 10 turns
            await self.persistence_manager.save_state(state)
    
    async def _update_metrics(self, frame_start_time: float) -> None:
        """Update heartbeat metrics"""
        frame_time = (time.time() - frame_start_time) * 1000
        
        # Update frame time accumulator for FPS calculation
        self.metrics.frame_time_ms = frame_time
        self.metrics.total_frames += 1
        self.metrics.total_time = time.time() - self.metrics.last_frame_time if self.metrics.last_frame_time > 0 else 0
        
        # Calculate FPS
        if self.metrics.total_time > 0:
            self.metrics.fps = self.metrics.total_frames / self.metrics.total_time
        
        # Update game state metrics
        current_state = self.dd_engine.get_current_state()
        current_state.performance_metrics["fps"] = self.metrics.fps
        current_state.performance_metrics["frame_time_ms"] = frame_time
    
    async def _frame_rate_limit(self, frame_start_time: float) -> None:
        """Limit frame rate to target FPS"""
        frame_time = time.time() - frame_start_time
        sleep_time = self.target_frame_time - frame_time
        
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks"""
        # World chunk pre-generation
        if self.world_engine:
            self.background_tasks["chunk_generation"] = asyncio.create_task(
                self._background_chunk_generation()
            )
        
        # Performance monitoring
        self.background_tasks["performance_monitor"] = asyncio.create_task(
            self._background_performance_monitor()
    )
    
    async def _background_chunk_generation(self) -> None:
        """Background task for chunk pre-generation"""
        logger.info("🌍 Background chunk generation started")
        
        while self.running:
            try:
                if not self.paused and self.world_engine:
                    # Get current player position
                    state = self.dd_engine.get_current_state()
                    player_pos = state.player_position
                    
                    # Pre-generate adjacent chunks
                    try:
                        await self.world_engine.pre_generate_chunks(player_pos)
                    except Exception as e:
                        logger.warning(f"⚠️ Chunk generation issue: {e}")
                
                # Run every 5 seconds
                await asyncio.sleep(5.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💥 Chunk generation error: {e}")
                await asyncio.sleep(10.0)  # Back off on error
        
        logger.info("🌍 Background chunk generation stopped")
    
    async def _background_performance_monitor(self) -> None:
        """Background task for performance monitoring"""
        logger.info("📊 Background performance monitoring started")
        
        while self.running:
            try:
                # Collect performance metrics
                metrics = await self._collect_performance_metrics()
                
                # Check for performance alerts
                await self._check_performance_alerts(metrics)
                
                # Update game state
                state = self.dd_engine.get_current_state()
                state.performance_metrics.update(metrics)
                
                # Run every 10 seconds
                await asyncio.sleep(10.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💥 Performance monitoring error: {e}")
                await asyncio.sleep(30.0)  # Back off on error
        
        logger.info("📊 Background performance monitoring stopped")
    
    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """Collect system performance metrics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "turn_time_ms": self.metrics.frame_time_ms  # Placeholder
        }
    
    async def _check_performance_alerts(self, metrics: Dict[str, float]) -> None:
        """Check for performance alerts"""
        # Memory alert
        if metrics.get("memory_mb", 0) > 512:
            logger.warning(f"⚠️ High memory usage: {metrics['memory_mb']:.1f}MB")
        
        # CPU alert
        if metrics.get("cpu_percent", 0) > 80:
            logger.warning(f"⚠️ High CPU usage: {metrics['cpu_percent']:.1f}%")
        
        # Frame time alert
        if metrics.get("frame_time_ms", 0) > 50:
            logger.warning(f"⚠️ High frame time: {metrics['frame_time_ms']:.1f}ms")
    
    def get_metrics(self) -> HeartbeatMetrics:
        """Get current heartbeat metrics"""
        return self.metrics
    
    def is_running(self) -> bool:
        """Check if heartbeat is running"""
        return self.running
    
    def is_paused(self) -> bool:
        """Check if heartbeat is paused"""
        return self.paused


# Global heartbeat instance
_heartbeat: Optional[HeartbeatController] = None


def get_heartbeat() -> HeartbeatController:
    """Get global heartbeat instance"""
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = HeartbeatController()
    return _heartbeat


async def initialize_heartbeat() -> HeartbeatController:
    """Initialize heartbeat system"""
    global _heartbeat
    _heartbeat = HeartbeatController()
    logger.info("🫀 Heartbeat system initialized")
    return _heartbeat
