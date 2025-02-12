# tests/unit/test_deployment.py

import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.ansible.deployment import (
    AnsibleDeployment,
    DeploymentConfig,
    DeploymentStatus,
    AnsibleError
)

@pytest.fixture
def deployment_config():
    return DeploymentConfig(
        deployment_id="test-deploy-001",
        station_id="test-station",
        environment="test",
        inventory_file="test_inventory.yml",
        playbook_file="test_playbook.yml",
        extra_vars={"test_var": "test_value"}
    )

@pytest.fixture
def ansible_deployment(tmp_path):
    return AnsibleDeployment(base_path=str(tmp_path))

@pytest.mark.asyncio
async def test_prepare_deployment(ansible_deployment, deployment_config, tmp_path):
    """Test deployment preparation"""
    # Create test files
    inventory_dir = tmp_path / "inventory"
    inventory_dir.mkdir()
    (inventory_dir / deployment_config.inventory_file).write_text("test inventory")
    
    await ansible_deployment.prepare_deployment(deployment_config)
    
    assert deployment_config.deployment_id in ansible_deployment.active_deployments
    assert (tmp_path / "tmp" / deployment_config.deployment_id).exists()

@pytest.mark.asyncio
async def test_run_deployment(ansible_deployment, deployment_config):
    """Test deployment execution"""
    await ansible_deployment.prepare_deployment(deployment_config)
    
    with patch('ansible_runner.run') as mock_run:
        mock_run.return_value.status = "successful"
        mock_run.return_value.rc = 0
        
        success = await ansible_deployment.run_deployment(deployment_config.deployment_id)
        
        assert success
        assert deployment_config.deployment_id in ansible_deployment.deployment_results
        assert ansible_deployment.deployment_results[deployment_config.deployment_id]["status"] == "success"

@pytest.mark.asyncio
async def test_deployment_failure(ansible_deployment, deployment_config):
    """Test handling of deployment failures"""
    await ansible_deployment.prepare_deployment(deployment_config)
    
    with patch('ansible_runner.run') as mock_run:
        mock_run.return_value.status = "failed"
        mock_run.return_value.rc = 1
        
        success = await ansible_deployment.run_deployment(deployment_config.deployment_id)
        
        assert not success
        assert ansible_deployment.deployment_results[deployment_config.deployment_id]["status"] == "failed"

@pytest.mark.asyncio
async def test_rollback_deployment(ansible_deployment, deployment_config):
    """Test deployment rollback"""
    await ansible_deployment.prepare_deployment(deployment_config)
    
    with patch('ansible_runner.run') as mock_run:
        mock_run.return_value.status = "successful"
        mock_run.return_value.rc = 0
        
        success = await ansible_deployment.rollback_deployment(deployment_config.deployment_id)
        
        assert success
        assert f"{deployment_config.deployment_id}-rollback" in ansible_deployment.active_deployments

@pytest.mark.asyncio
async def test_cleanup_deployment(ansible_deployment, deployment_config, tmp_path):
    """Test deployment cleanup"""
    await ansible_deployment.prepare_deployment(deployment_config)
    deploy_dir = tmp_path / "tmp" / deployment_config.deployment_id
    
    assert deploy_dir.exists()
    
    await ansible_deployment._cleanup_deployment(deployment_config.deployment_id)
    
    assert not deploy_dir.exists()

@pytest.mark.asyncio
async def test_invalid_deployment_id(ansible_deployment):
    """Test handling of invalid deployment IDs"""
    with pytest.raises(AnsibleError):
        await ansible_deployment.run_deployment("nonexistent-deployment")

@pytest.mark.asyncio
async def test_prepare_variables(ansible_deployment, deployment_config, tmp_path):
    """Test variable preparation"""
    await ansible_deployment.prepare_deployment(deployment_config)
    
    deploy_dir = tmp_path / "tmp" / deployment_config.deployment_id
    vars_dir = deploy_dir / "vars"
    
    assert vars_dir.exists()
    assert (vars_dir / "extra_vars.yml").exists()

@pytest.mark.asyncio
async def test_concurrent_deployments(ansible_deployment):
    """Test handling multiple concurrent deployments"""
    configs = [
        DeploymentConfig(
            deployment_id=f"test-deploy-{i}",
            station_id=f"test-station-{i}",
            environment="test",
            inventory_file="test_inventory.yml",
            playbook_file="test_playbook.yml"
        )
        for i in range(3)
    ]
    
    # Prepare all deployments
    prepare_tasks = [
        ansible_deployment.prepare_deployment(config)
        for config in configs
    ]
    await asyncio.gather(*prepare_tasks)
    
    # Run all deployments
    with patch('ansible_runner.run') as mock_run:
        mock_run.return_value.status = "successful"
        mock_run.return_value.rc = 0
        
        run_tasks = [
            ansible_deployment.run_deployment(config.deployment_id)
            for config in configs
        ]
        results = await asyncio.gather(*run_tasks)
        
        assert all(results)
        assert all(
            config.deployment_id in ansible_deployment.deployment_results
            for config in configs
        )

@pytest.mark.asyncio
async def test_deployment_status_tracking(ansible_deployment, deployment_config):
    """Test deployment status tracking"""
    await ansible_deployment.prepare_deployment(deployment_config)
    
    with patch('ansible_runner.run') as mock_run:
        mock_run.return_value.status = "successful"
        mock_run.return_value.rc = 0
        
        await ansible_deployment.run_deployment(deployment_config.deployment_id)
        
        status = await ansible_deployment.get_deployment_status(deployment_config.deployment_id)
        
        assert status is not None
        assert status["status"] == "success"
        assert "completed_at" in status

@pytest.mark.asyncio
async def test_error_handling(ansible_deployment, deployment_config):
    """Test error handling in deployment process"""
    # Test preparation error
    with patch.object(ansible_deployment, '_prepare_inventory', return_value=False):
        with pytest.raises(AnsibleError):
            await ansible_deployment.prepare_deployment(deployment_config)
    
    # Test execution error
    await ansible_deployment.prepare_deployment(deployment_config)
    with patch('ansible_runner.run', side_effect=Exception("Ansible error")):
        success = await ansible_deployment.run_deployment(deployment_config.deployment_id)
        assert not success
        assert ansible_deployment.deployment_results[deployment_config.deployment_id]["status"] == "failed"

if __name__ == '__main__':
    pytest.main([__file__])
