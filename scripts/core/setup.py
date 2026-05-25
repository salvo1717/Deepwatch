import subprocess
import sys
import os
import importlib.metadata
import platform

def is_installed(package_name):
    try:
        importlib.metadata.distribution(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False

def check_torch_flavor():
    try:
        import torch
        v = torch.__version__
        if torch.cuda.is_available(): return "CUDA"
        if "+cu" in v: return "CUDA_NOT_ACTIVE"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available(): return "MPS"
        return "CPU"
    except: return None

def install_all(libs, gpu_mode="CPU", show_progress=False):
    if not libs:
        return
    
    unique_libs = list(dict.fromkeys(libs))
    
    if not is_installed("uv"):
        print("--> Setup motore uv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"], stdout=subprocess.DEVNULL)

    # --- LOGICA DI INSTALLAZIONE A DUE FASI  ---
    if gpu_mode in ["INTEL", "CPU"]:
        torch_libs = [l for l in unique_libs if l in ["torch", "torchvision"]]
        other_libs = [l for l in unique_libs if l not in ["torch", "torchvision"]]
        
        # FASE 1: Installazione atomica di Torch CPU-Only per evitare conflitti e bloat su Intel/CPU
        if torch_libs:
            print(f"--> [UV] Fase 1: Installazione PyTorch CPU-Only...")
            cmd1 = [sys.executable, "-m", "uv", "pip", "install", "--index-url", "https://download.pytorch.org/whl/cpu"] + torch_libs
            subprocess.check_call(cmd1, stdout=None if show_progress else subprocess.DEVNULL)
        
        # FASE 2: Installazione del resto delle dipendenze (OpenVINO, NNCF, Ultralytics, ecc.) in batch standard
        if other_libs:
            print(f"--> [UV] Fase 2: Installazione dipendenze...")
            cmd2 = [sys.executable, "-m", "uv", "pip", "install"] + other_libs
            subprocess.check_call(cmd2, stdout=None if show_progress else subprocess.DEVNULL)
            
    else:
        # Per NVIDIA/AMD/ALTRO: installazione batch standard
        indices = []
        if gpu_mode == "NVIDIA":
            indices = ["--extra-index-url", "https://download.pytorch.org/whl/cu121"]
        elif gpu_mode == "AMD_LINUX":
            indices = ["--extra-index-url", "https://download.pytorch.org/whl/rocm6.1"]
            
        print(f"--> [UV] Installazione Concorrente ({gpu_mode})...")
        cmd = [sys.executable, "-m", "uv", "pip", "install"] + indices + unique_libs
        subprocess.check_call(cmd, stdout=None if show_progress else subprocess.DEVNULL)

def check_hardware():
    os_name = platform.system()
    try:
        if os_name == "Windows":
            output = subprocess.check_output(["powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"], stderr=subprocess.DEVNULL).decode().lower()
        elif os_name == "Linux":
            output = subprocess.check_output(["lspci"], stderr=subprocess.DEVNULL).decode().lower()
        elif os_name == "Darwin":
            if platform.processor() == 'arm' or platform.machine() == 'arm64': return "APPLE_SILICON"
            return "CPU"
        else: output = ""
            
        if any(x in output for x in ["apple", "m1", "m2", "m3"]): return "APPLE_SILICON"
        if "intel" in output and any(x in output for x in ["ultra", "arc", "iris"]): return "INTEL"
        if "nvidia" in output and ("vga" in output or "3d" in output or "graphics" in output or os_name == "Windows"): return "NVIDIA"
        if "amd" in output or "radeon" in output: return "AMD"
        if "intel" in output: return "INTEL"
        return "CPU"
    except: return "CPU"

def main():
    os_name = platform.system()
    gpu_type = check_hardware()
    print(f"🔍 Analisi Hardware: {gpu_type} su {os_name}")
    
    current_flavor = check_torch_flavor()
    
    # RIMOZIONE CUDA SE PRESENTE SU INTEL PER EVITARE BLOAT E CONFLITTI 
    if gpu_type in ["INTEL", "CPU"] and current_flavor in ["CUDA", "CUDA_NOT_ACTIVE"]:
        print("   [!] Rilevato PyTorch CUDA su sistema Intel. Rimozione forzata per eliminare 2GB di bloat...")
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision"], stdout=subprocess.DEVNULL)
        current_flavor = None

    to_install = []
    
    if current_flavor is None:
        to_install.extend(["torch", "torchvision"])
    
    if gpu_type == "INTEL":
        if not is_installed("openvino"): to_install.append("openvino>=2024.0.0")
        if not is_installed("nncf"): to_install.append("nncf")
    elif gpu_type == "AMD" and os_name == "Windows":
        if not is_installed("onnxruntime-directml"): to_install.append("onnxruntime-directml")

    if not is_installed("ultralytics"): to_install.append("ultralytics")
    if not is_installed("opencv-python"): to_install.append("opencv-python")
    if not is_installed("PyQt6"): to_install.append("PyQt6")
    if not is_installed("qt-material"): to_install.append("qt-material")
    if not is_installed("python-dotenv"): to_install.append("python-dotenv")
    if not is_installed("motor"): to_install.append("motor")
    if not is_installed("beanie"): to_install.append("beanie")
    if not is_installed("psutil"): to_install.append("psutil")
    if not is_installed("numpy"): to_install.append("numpy")
    if not is_installed("onnxruntime"): to_install.append("onnxruntime")
    if not is_installed("pillow"): to_install.append("pillow")

    if to_install:
        mode = gpu_type
        if gpu_type == "AMD" and os_name == "Linux": mode = "AMD_LINUX"
        install_all(to_install, gpu_mode=mode, show_progress=True)
    else:
        print(f"   [OK] Sistema già ottimizzato (Flavor: {current_flavor}).")

    print("\n✅ Setup completato.")

if __name__ == "__main__":
    main()
