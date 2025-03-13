import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Any

def execute_command(
    command: str, 
    working_dir: str = None, 
    timeout: int = 60,
    capture_output: bool = True
) -> Dict[str, Any]:
    """
    Execute an arbitrary CLI command
    
    Args:
        command: The command to execute
        working_dir: Directory to execute the command in (default: current directory)
        timeout: Maximum execution time in seconds (default: 60)
        capture_output: Whether to capture and return command output (default: True)
        
    Returns:
        Dict containing execution status, output, and error message if any
    """
    try:
        # Set working directory if provided, otherwise use current
        cwd = working_dir if working_dir else os.getcwd()
        
        # Prepare directory if it doesn't exist
        if not os.path.exists(cwd):
            os.makedirs(cwd, exist_ok=True)
            
        # Execute the command
        if capture_output:
            # Use subprocess.run with output capture
            process = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Prepare result
            result = {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "command": command,
                "working_dir": cwd
            }
        else:
            # Use os.system for commands that need direct terminal interaction
            exit_code = os.system(f"cd {shlex.quote(cwd)} && {command}")
            
            result = {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "command": command,
                "working_dir": cwd,
                "message": "Command executed without capturing output"
            }
            
        return result
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }


def install_package(
    package_name: str,
    update_first: bool = True,
    use_sudo: bool = True
) -> Dict[str, Any]:
    """
    Install a package using apt-get
    
    Args:
        package_name: Name of the package to install
        update_first: Whether to run apt-get update first (default: True)
        use_sudo: Whether to use sudo for installation (default: True)
        
    Returns:
        Dict containing installation status and output
    """
    try:
        results = []
        
        # Get sudo password if needed and available
        sudo_prefix = "sudo -S " if use_sudo else ""
        
        # Update package list if requested
        if update_first:
            update_cmd = f"{sudo_prefix}apt-get update"
            update_result = execute_command(update_cmd)
            results.append({"operation": "update", **update_result})
            
            # Return early if update failed
            if not update_result["success"]:
                return {
                    "success": False,
                    "error": "Package update failed",
                    "results": results
                }
        
        # Install the package
        install_cmd = f'{sudo_prefix}apt-get install -y {package_name}'
        install_result = execute_command(install_cmd)
        results.append({"operation": "install", **install_result})
        
        return {
            "success": install_result["success"],
            "package": package_name,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "package": package_name
        }


def create_file(
    file_path: str,
    content: str,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Create or update a file with the specified content
    
    Args:
        file_path: Path to the file to create/update
        content: Content to write to the file
        overwrite: Whether to overwrite existing file (default: True)
        
    Returns:
        Dict containing file operation status
    """
    try:
        path = Path(file_path)
        
        # Check if file exists and overwrite is disabled
        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File already exists: {file_path}",
                "message": "Set overwrite=True to replace the file"
            }
            
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(path, 'w') as f:
            f.write(content)
            
        # Get file statistics
        stats = path.stat()
        
        return {
            "success": True,
            "path": str(path.absolute()),
            "size": stats.st_size,
            "message": f"File created successfully at {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": file_path
        }


def read_file(
    file_path: str,
    max_size_kb: int = 1024
) -> Dict[str, Any]:
    """
    Read the content of a file
    
    Args:
        file_path: Path to the file to read
        max_size_kb: Maximum file size to read in KB (default: 1024)
        
    Returns:
        Dict containing file content and metadata
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
            
        # Get file stats
        stats = path.stat()
        
        # Check file size
        if stats.st_size > max_size_kb * 1024:
            return {
                "success": False,
                "error": f"File exceeds maximum size of {max_size_kb}KB",
                "size_kb": stats.st_size / 1024,
                "max_size_kb": max_size_kb
            }
            
        # Read and return content
        content = path.read_text()
        
        return {
            "success": True,
            "path": str(path.absolute()),
            "content": content,
            "size_kb": stats.st_size / 1024,
            "message": f"File read successfully from {file_path}"
        }
        
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"File contains non-text content: {file_path}",
            "message": "This function can only read text files"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": file_path
        }