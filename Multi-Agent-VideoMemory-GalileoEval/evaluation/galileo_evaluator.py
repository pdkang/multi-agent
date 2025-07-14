# evaluation/galileo_evaluator.py
import os
import galileo
from galileo import galileo_context, log
from galileo.handlers.langchain import GalileoCallback
from datetime import datetime
from dotenv import load_dotenv
import json
import atexit
import signal
import sys
import threading

class GalileoEvaluator:
    # Class-level singleton context
    _global_context = None
    _context_initialized = False
    _session_id = None
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('GALILEO_API_KEY')
        self.project_id = os.getenv('GALILEO_PROJECT_ID')
        self.log_stream = os.getenv('GALILEO_LOG_STREAM')
        
        # Debug: Print the values being used
        print(f"🔧 Galileo Config - API Key: {'✅' if self.api_key else '❌'}")
        print(f"🔧 Galileo Config - Project ID: {self.project_id}")
        print(f"🔧 Galileo Config - Log Stream: {self.log_stream}")
        
        # Set environment variables for Galileo
        os.environ['GALILEO_API_KEY'] = self.api_key
        os.environ['GALILEO_PROJECT_ID'] = self.project_id
        os.environ['GALILEO_LOG_STREAM'] = self.log_stream
        
        # Use singleton context
        self.context = GalileoEvaluator._global_context
        print(f"🏗️ GalileoEvaluator instance created: {id(self)}")
        print(f"   - Process ID: {os.getpid()}")
        print(f"   - Thread ID: {threading.get_ident()}")
        print(f"   - Global context exists: {GalileoEvaluator._global_context is not None}")
        print(f"   - Context assigned: {self.context is not None}")
        if self.context:
            print(f"   - Context ID: {id(self.context)}")
        
        if not GalileoEvaluator._context_initialized:
            print("   - First instance, setting up cleanup handlers")
            self._setup_cleanup_handlers()
            GalileoEvaluator._context_initialized = True
        else:
            print("   - Reusing existing cleanup handlers")
        
    def _setup_cleanup_handlers(self):
        """Setup automatic cleanup handlers for graceful shutdown"""
        # Register cleanup function to run on normal exit
        atexit.register(self._cleanup_on_exit)
        
        # Only register signal handlers if we're in the main thread
        import threading
        if threading.current_thread() is threading.main_thread():
            try:
                # Register signal handlers for graceful shutdown
                def signal_handler(signum, frame):
                    print(f"\n🔄 Received signal {signum}, cleaning up Galileo context...")
                    self._cleanup_on_exit()
                    sys.exit(0)
                
                # Register handlers for common termination signals
                signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
                signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
                print("✅ Signal handlers registered (main thread)")
            except Exception as e:
                print(f"⚠️ Could not register signal handlers: {e}")
        else:
            print("ℹ️ Skipping signal handlers (not in main thread)")
        
    def _cleanup_on_exit(self):
        """Cleanup function called on exit"""
        try:
            if self.context:
                print("🔄 Flushing Galileo traces...")
                self.end_context()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
        
    def start_context(self, project_name=None, log_stream=None):
        """Start a Galileo context for tracking using the context manager pattern"""
        try:
            # Check if global context already exists
            if GalileoEvaluator._global_context is not None:
                session_id = GalileoEvaluator._session_id or "unknown"
                print(f"ℹ️ Galileo context already exists, reusing... (Global: {id(GalileoEvaluator._global_context)}, session_id: {session_id})")
                self.context = GalileoEvaluator._global_context
                return True
            
            # Always use the environment variables unless explicitly overridden
            project = project_name or self.project_id
            stream = log_stream or self.log_stream
            
            if not project:
                print("❌ No project ID available")
                return False
                
            if not stream:
                print("❌ No log stream available")
                return False
            
            # Start Galileo context using context manager pattern
            import uuid
            session_id = str(uuid.uuid4())[:8]
            GalileoEvaluator._session_id = session_id
            
            print(f"🆕 Creating NEW Galileo context: project={project}, stream={stream}, session_id={session_id}")
            
            # Try alternative initialization method
            try:
                # Method 1: Standard context manager
                self.context = galileo_context(project=project, log_stream=stream)
                self.context.__enter__()
                print(f"✅ Galileo context started using standard method: {id(self.context)}")
            except Exception as context_error:
                print(f"⚠️ Standard context failed: {context_error}")
                try:
                    # Method 2: Direct initialization
                    import galileo
                    galileo.init(project=project, log_stream=stream)
                    self.context = galileo_context(project=project, log_stream=stream)
                    self.context.__enter__()
                    print(f"✅ Galileo context started using direct init: {id(self.context)}")
                except Exception as init_error:
                    print(f"⚠️ Direct init failed: {init_error}")
                    # Method 3: Minimal initialization
                    self.context = galileo_context(project=project, log_stream=stream)
                    self.context.__enter__()
                    print(f"✅ Galileo context started using minimal method: {id(self.context)}")
            
            # Store as global singleton
            GalileoEvaluator._global_context = self.context
            print(f"✅ Galileo context started and stored as global: {id(self.context)}, session_id={session_id}")
            return True
                
        except Exception as e:
            print(f"❌ Failed to start Galileo context: {str(e)}")
            return False
    
    def flush_context(self):
        """Manually flush the current context to send traces immediately"""
        try:
            if self.context:
                # Force flush by temporarily ending and restarting context
                print("🔄 Flushing Galileo context...")
                self.context.__exit__(None, None, None)
                
                # Restart context immediately with same session ID
                project = self.project_id
                stream = self.log_stream
                session_id = GalileoEvaluator._session_id  # Preserve session ID
                self.context = galileo_context(project=project, log_stream=stream)
                self.context.__enter__()
                
                # Update global singleton
                GalileoEvaluator._global_context = self.context
                
                print(f"✅ Galileo context flushed and restarted (session_id: {session_id})")
                return True
        except Exception as e:
            print(f"❌ Failed to flush Galileo context: {str(e)}")
            return False
    
    def gentle_flush(self):
        """Gentle flush that doesn't restart the context"""
        try:
            if self.context:
                print("🔄 Gentle flush - triggering trace delivery...")
                # Force a flush without restarting the context
                # This ensures traces are sent while maintaining session continuity
                if hasattr(self.context, '_client') and self.context._client:
                    # Try to flush the client directly if available
                    try:
                        self.context._client.flush()
                        print("✅ Traces flushed via client")
                    except:
                        pass
                
                # Let Galileo handle the rest naturally
                return True
        except Exception as e:
            print(f"❌ Failed to gentle flush: {str(e)}")
            return False
    
    def check_trace_status(self):
        """Check if traces are being sent to Galileo"""
        try:
            if self.context:
                session_id = GalileoEvaluator._session_id or "unknown"
                print(f"🔍 Checking trace status for session: {session_id}")
                print(f"   - Context active: {self.context is not None}")
                print(f"   - Global context: {GalileoEvaluator._global_context is not None}")
                print(f"   - Same context: {self.context is GalileoEvaluator._global_context}")
                return True
        except Exception as e:
            print(f"❌ Failed to check trace status: {str(e)}")
            return False
    
    def flush_after_query(self):
        """Strategic flush after a complete query processing cycle"""
        try:
            if self.context:
                print("🔄 Flushing traces after complete query processing...")
                session_id = GalileoEvaluator._session_id or "unknown"
                print(f"ℹ️ Ensuring traces are sent to Galileo (session_id: {session_id})")
                
                # Force a flush by temporarily ending and restarting the context
                # This ensures traces are sent while maintaining session continuity
                print("🔄 Forcing trace delivery with context restart...")
                return self.flush_context()
                
        except Exception as e:
            print(f"❌ Failed to flush after query: {str(e)}")
            return False
    
    def is_context_reused(self):
        """Check if this instance is reusing an existing context"""
        return self.context is not None and GalileoEvaluator._global_context is self.context
    
    @classmethod
    def reset_global_context(cls):
        """Reset the global context (useful for testing or debugging)"""
        if cls._global_context:
            try:
                cls._global_context.__exit__(None, None, None)
            except:
                pass
            cls._global_context = None
            print("🔄 Global Galileo context reset")
    
    def get_callback(self):
        """Get the Galileo callback for use with LangChain"""
        return GalileoCallback()
    
    @log(span_type="llm", name="query_processing")
    def log_query(self, query, response, metrics=None):
        """Log a query and response to Galileo using @log decorator"""
        try:
            # The @log decorator automatically creates a proper span
            # Add metrics as attributes if provided
            if metrics:
                # Log metrics as part of the span
                for key, value in metrics.items():
                    print(f"Metric - {key}: {value}")
            
            # Only flush after the final query log (not after every intermediate log)
            # This prevents duplicate traces and maintains proper span hierarchy
            session_id = GalileoEvaluator._session_id or "unknown"
            print(f"🔄 Final query logged, traces should be sent to Galileo (session_id: {session_id})")
            
            # Return the response to be logged as the span output
            return response
            
        except Exception as e:
            print(f"❌ Failed to log query to Galileo: {str(e)}")
            return response
    
    @log(span_type="tool", name="agent_processing")
    def log_agent_span(self, agent_name, input_data, output_data, metrics=None):
        """Log an agent's processing span using @log decorator"""
        try:
            # The @log decorator automatically creates a proper span
            # Add metrics as attributes if provided
            if metrics:
                # Log metrics as part of the span
                for key, value in metrics.items():
                    print(f"Agent Metric - {key}: {value}")
            
            # Don't flush after every agent span - let the context handle it naturally
            # This prevents duplicate traces and maintains proper span hierarchy
            
            # Return the output to be logged as the span output
            return output_data
            
        except Exception as e:
            print(f"❌ Failed to log agent span: {str(e)}")
            return output_data
    
    @log(span_type="tool", name="fallback_decision")
    def log_fallback_decision(self, from_agent, to_agent, reason):
        """Log when orchestrator falls back to web search using @log decorator"""
        try:
            # The @log decorator automatically creates a proper span
            decision_info = f"Fallback from {from_agent} to {to_agent}: {reason}"
            print(f"Fallback Decision: {decision_info}")
            
            # Don't flush after fallback decisions - let the context handle it naturally
            # This prevents duplicate traces and maintains proper span hierarchy
            
            return decision_info
            
        except Exception as e:
            print(f"❌ Failed to log fallback decision: {str(e)}")
            return f"Fallback error: {str(e)}"
    
    def end_context(self):
        """End the current Galileo context"""
        try:
            if self.context:
                self.context.__exit__(None, None, None)
                self.context = None
                # Clear global singleton
                GalileoEvaluator._global_context = None
                print("✅ Galileo context ended")
        except Exception as e:
            print(f"❌ Failed to end Galileo context: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self._cleanup_on_exit()
    
    # Legacy methods for backward compatibility
    def start_session(self, session_name=None, external_id=None):
        """Legacy method - now uses context-based approach"""
        return self.start_context()
    
    def end_session(self):
        """Legacy method - now uses context-based approach"""
        return self.end_context()