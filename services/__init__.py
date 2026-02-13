"""Services Auto-Loader - Zero-configuration plugin system.

Drop a service folder into services/ with an endpoints.py exporting 'router'.
"""

import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter

logger = logging.getLogger(__name__)


class ServiceLoader:
    """Service auto-loader with discovery and validation."""
    
    def __init__(self):
        self.services_dir = Path(__file__).parent
        self.loaded_services: Dict[str, Dict[str, Any]] = {}
        self.failed_services: Dict[str, str] = {}
    
    def discover_services(self) -> List[Path]:
        """Discover all valid service directories."""
        service_folders = []
        
        if not self.services_dir.exists():
            logger.warning(f"Services directory not found: {self.services_dir}")
            return service_folders
        
        for item in self.services_dir.iterdir():
            # Skip special folders and files
            if item.name.startswith('_') or item.name.startswith('.'):
                continue
            
            # Must be a directory
            if not item.is_dir():
                continue
            
            # Must have endpoints.py
            endpoints_file = item / 'endpoints.py'
            if not endpoints_file.exists():
                logger.debug(f"Skipping {item.name}: No endpoints.py found")
                continue
            
            service_folders.append(item)
            logger.debug(f"Discovered service candidate: {item.name}")
        
        return service_folders
    
    def load_service(self, service_path: Path) -> Optional[APIRouter]:
        """Load a single service and return its router."""
        service_name = service_path.name
        
        try:
            # Import service package and call setup() if defined
            service_pkg = importlib.import_module(f"services.{service_name}")
            if hasattr(service_pkg, 'setup'):
                service_pkg.setup()
            
            # Import the endpoints module
            module_path = f"services.{service_name}.endpoints"
            logger.debug(f"Importing {module_path}...")
            module = importlib.import_module(module_path)
            
            # Validate router exists
            if not hasattr(module, 'router'):
                error_msg = "No 'router' variable found in endpoints.py"
                logger.error(f"✗ {service_name}: {error_msg}")
                self.failed_services[service_name] = error_msg
                return None
            
            router = getattr(module, 'router')
            
            # Validate it's actually a router
            if not isinstance(router, APIRouter):
                error_msg = "'router' is not a FastAPI APIRouter instance"
                logger.error(f"✗ {service_name}: {error_msg}")
                self.failed_services[service_name] = error_msg
                return None
            
            # Extract metadata
            prefix = getattr(router, 'prefix', '/')
            tags = getattr(router, 'tags', [])
            
            # Count routes
            route_count = len(router.routes)
            
            # Store service info
            self.loaded_services[service_name] = {
                'name': service_name,
                'router': router,
                'prefix': prefix,
                'tags': tags,
                'routes': route_count,
                'path': str(service_path)
            }
            
            logger.info(f"✓ {service_name:<15} │ {prefix:<20} │ {route_count} routes │ {tags}")
            return router
        
        except ImportError as e:
            error_msg = f"Import failed: {str(e)}"
            logger.error(f"✗ {service_name}: {error_msg}")
            self.failed_services[service_name] = error_msg
            return None
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"✗ {service_name}: {error_msg}", exc_info=True)
            self.failed_services[service_name] = error_msg
            return None
    
    def load_all_services(self) -> List[APIRouter]:
        """Discover and load all services."""
        logger.info("=" * 80)
        logger.info("SERVICE AUTO-LOADER: Starting discovery...")
        logger.info("=" * 80)
        
        # Discover services
        service_paths = self.discover_services()
        
        if not service_paths:
            logger.warning("No services found in services/ directory")
            return []
        
        logger.info(f"Found {len(service_paths)} service(s) to load")
        logger.info("-" * 80)
        logger.info(f"{'SERVICE':<15} │ {'ENDPOINT PREFIX':<20} │ {'INFO'}")
        logger.info("-" * 80)
        
        # Load each service
        routers = []
        for service_path in sorted(service_paths):
            router = self.load_service(service_path)
            if router:
                routers.append(router)
        
        logger.info("-" * 80)
        logger.info(f"✓ Successfully loaded: {len(routers)}/{len(service_paths)} services")
        
        if self.failed_services:
            logger.warning(f"✗ Failed to load: {len(self.failed_services)} service(s)")
            for service_name, error in self.failed_services.items():
                logger.warning(f"  - {service_name}: {error}")
        
        logger.info("=" * 80)
        
        return routers
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about loaded services."""
        return {
            'total_services': len(self.loaded_services),
            'failed_services': len(self.failed_services),
            'services': self.loaded_services,
            'failures': self.failed_services
        }


# Global service loader instance
_service_loader = ServiceLoader()


def load_service_routers() -> List[APIRouter]:
    """Load all service routers (main entry point)."""
    return _service_loader.load_all_services()


def get_loaded_services() -> Dict[str, Any]:
    """Get loaded service info."""
    return _service_loader.get_service_info()

