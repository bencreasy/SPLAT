# src/ansible/deployment.py

import os
import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List, Any
import yaml
import json
import ansible_runner
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

from . import AnsibleError, AnsibleConfigError, AnsibleExecutionError

class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class DeploymentConfig:
    """Configuration for a deployment"""
    deployment_id: str
    station_id: str
    environment: str
    inventory_file: str
    playbook_file: str
    vars_file: Optional[str] = None
    extra_vars: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    skip_tags: Optional[List[str]] = None

class AnsibleDeployment:
    """
    Handles Ansible-based deployments for SPLAT Ground Control stations
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.logger = logging.getLogger('FlightDirector.Ansible')
        self.active_deployments: Dict[str, DeploymentConfig] = {}
        self.deployment_results: Dict[str, Dict[str, Any]] = {}
        
        # Ensure required directories exist
        self._init_directories()

    def _init_directories(self) -> None:
        """Initialize required directory structure"""
        directories = [
            self.base_path / "inventory",
            self.base_path / "playbooks",
            self.base_path / "roles",
            self.base_path / "vars",
            self.base_path / "tmp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def prepare_deployment(self, config: DeploymentConfig) -> None:
        """
        Prepare for deployment by setting up necessary files and configurations
        """
        try:
            # Create deployment working directory
            deploy_dir = self.base_path / "tmp" / config.deployment_id
            deploy_dir.mkdir(exist_ok=True)
            
            # Copy inventory file
            if not await self._prepare_inventory(config, deploy_dir):
                raise AnsibleConfigError("Failed to prepare inventory")
            
            # Copy playbook file
            if not await self._prepare_playbook(config, deploy_dir):
                raise AnsibleConfigError("Failed to prepare playbook")
            
            # Prepare variables
            if not await self._prepare_variables(config, deploy_dir):
                raise AnsibleConfigError("Failed to prepare variables")
            
            self.active_deployments[config.deployment_id] = config
            self.logger.info(f"Deployment {config.deployment_id} prepared successfully")
            
        except Exception as e:
            self.logger.error(f"Error preparing deployment: {str(e)}")
            raise AnsibleConfigError(f"Deployment preparation failed: {str(e)}")

    async def run_deployment(self, deployment_id: str) -> bool:
        """
        Execute an Ansible deployment
        """
        if deployment_id not in self.active_deployments:
            raise AnsibleError(f"Deployment {deployment_id} not found")
            
        config = self.active_deployments[deployment_id]
        deploy_dir = self.base_path / "tmp" / deployment_id
        
        try:
            self.logger.info(f"Starting deployment {deployment_id}")
            
            # Prepare runtime configuration
            runner_config = {
                "private_data_dir": str(deploy_dir),
                "playbook": config.playbook_file,
                "inventory": config.inventory_file,
                "verbosity": 1
            }
            
            if config.extra_vars:
                runner_config["extravars"] = config.extra_vars
            
            if config.tags:
                runner_config["tags"] = config.tags
            
            if config.skip_tags:
                runner_config["skip_tags"] = config.skip_tags
            
            # Run the deployment
            runner = ansible_runner.run(**runner_config)
            
            # Store results
            self.deployment_results[deployment_id] = {
                "status": "success" if runner.status == "successful" else "failed",
                "rc": runner.rc,
                "stats": runner.stats,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            if runner.status == "successful":
                self.logger.info(f"Deployment {deployment_id} completed successfully")
                return True
            else:
                self.logger.error(f"Deployment {deployment_id} failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in deployment {deployment_id}: {str(e)}")
            self.deployment_results[deployment_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
            raise AnsibleExecutionError(f"Deployment execution failed: {str(e)}")
        
        finally:
            # Cleanup if needed
            if not self.config.get("keep_deployment_files", False):
                await self._cleanup_deployment(deployment_id)

    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a deployment
        """
        return self.deployment_results.get(deployment_id)

    async def rollback_deployment(self, deployment_id: str) -> bool:
        """
        Rollback a deployment
        """
        if deployment_id not in self.active_deployments:
            raise AnsibleError(f"Deployment {deployment_id} not found")
            
        config = self.active_deployments[deployment_id]
        
        try:
            # Prepare rollback configuration
            rollback_config = DeploymentConfig(
                deployment_id=f"{deployment_id}-rollback",
                station_id=config.station_id,
                environment=config.environment,
                inventory_file=config.inventory_file,
                playbook_file="rollback.yml",
                extra_vars={"original_deployment": deployment_id}
            )
            
            # Execute rollback
            await self.prepare_deployment(rollback_config)
            success = await self.run_deployment(rollback_config.deployment_id)
            
            if success:
                self.logger.info(f"Rollback of deployment {deployment_id} completed successfully")
            else:
                self.logger.error(f"Rollback of deployment {deployment_id} failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error rolling back deployment {deployment_id}: {str(e)}")
            raise AnsibleExecutionError(f"Rollback failed: {str(e)}")

    async def _prepare_inventory(self, config: DeploymentConfig, deploy_dir: Path) -> bool:
        """Prepare inventory file for deployment"""
        try:
            src_path = self.base_path / "inventory" / config.inventory_file
            dst_path = deploy_dir / "inventory"
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                return True
            else:
                self.logger.error(f"Inventory file not found: {src_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error preparing inventory: {str(e)}")
            return False

    async def _prepare_playbook(self, config: DeploymentConfig, deploy_dir: Path) -> bool:
        """Prepare playbook file for deployment"""
        try:
            src_path = self.base_path / "playbooks" / config.playbook_file
            dst_path = deploy_dir / "project"
            dst_path.mkdir(exist_ok=True)
            
            if src_path.exists():
                shutil.copy2(src_path, dst_path / config.playbook_file)
                return True
            else:
                self.logger.error(f"Playbook file not found: {src_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error preparing playbook: {str(e)}")
            return False

    async def _prepare_variables(self, config: DeploymentConfig, deploy_dir: Path) -> bool:
        """Prepare variables for deployment"""
        try:
            vars_dir = deploy_dir / "vars"
            vars_dir.mkdir(exist_ok=True)
            
            # Handle vars file if specified
            if config.vars_file:
                src_path = self.base_path / "vars" / config.vars_file
                if src_path.exists():
                    shutil.copy2(src_path, vars_dir / config.vars_file)
            
            # Handle extra vars
            if config.extra_vars:
                with open(vars_dir / "extra_vars.yml", 'w') as f:
                    yaml.dump(config.extra_vars, f)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing variables: {str(e)}")
            return False

    async def _cleanup_deployment(self, deployment_id: str) -> None:
        """Clean up deployment files"""
        try:
            deploy_dir = self.base_path / "tmp" / deployment_id
            if deploy_dir.exists():
                shutil.rmtree(deploy_dir)
            
            self.logger.debug(f"Cleaned up deployment directory for {deployment_id}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up deployment {deployment_id}: {str(e)}")

# Helper functions for common deployment tasks
async def deploy_ground_control(
    ansible: AnsibleDeployment,
    station_id: str,
    environment: str,
    extra_vars: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Helper function to deploy a Ground Control station
    """
    deployment_id = f"gc-{station_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    config = DeploymentConfig(
        deployment_id=deployment_id,
        station_id=station_id,
        environment=environment,
        inventory_file="ground_control.yml",
        playbook_file="site.yml",
        extra_vars=extra_vars
    )
    
    try:
        await ansible.prepare_deployment(config)
        return await ansible.run_deployment(deployment_id)
    except AnsibleError as e:
        logging.error(f"Failed to deploy Ground Control station {station_id}: {str(e)}")
        return False

async def deploy_launchpad(
    ansible: AnsibleDeployment,
    station_id: str,
    environment: str,
    extra_vars: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Helper function to deploy LaunchPad configuration
    """
    deployment_id = f"lp-{station_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    config = DeploymentConfig(
        deployment_id=deployment_id,
        station_id=station_id,
        environment=environment,
        inventory_file="ground_control.yml",
        playbook_file="launchpad.yml",
        extra_vars=extra_vars
    )
    
    try:
        await ansible.prepare_deployment(config)
        return await ansible.run_deployment(deployment_id)
    except AnsibleError as e:
        logging.error(f"Failed to deploy LaunchPad for station {station_id}: {str(e)}")
        return False
