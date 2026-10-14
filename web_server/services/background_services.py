import asyncio
import time
import psutil

from repositories.current_instance_repositories import CurrentInstanceRepositories

# ---------- GPU INIT ----------
try:
    from pynvml import (
        nvmlInit,
        nvmlShutdown,
        nvmlDeviceGetCount,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetUtilizationRates,
        nvmlDeviceGetMemoryInfo,
        nvmlDeviceGetTemperature,
        NVML_TEMPERATURE_GPU
    )

    nvmlInit()
    GPU_COUNT = nvmlDeviceGetCount()
    GPU_AVAILABLE = GPU_COUNT > 0

except Exception as e:
    print("NVML INIT FAILED:", e)
    GPU_AVAILABLE = False
    GPU_COUNT = 0


class BackgroundService:

    @staticmethod
    async def monitor_system_stats():
        system_monitor = SystemMonitor()

        while True:
            await asyncio.sleep(1)

            if not CurrentInstanceRepositories.monitor_system:
                break

            stats = system_monitor.collect()
            CurrentInstanceRepositories.system_stats = stats
            # print(stats)

            from socket_controller.admin_dashboard_socket_controller import admin_dashboard_manager
            await admin_dashboard_manager.send_json({
                "type": "system_stats",
                "object": stats
            })

            # -------- CAMERA STATUS --------
            from repositories.camera_repositories import CameraRepository
            from socket_controller.camera_status_socket_controller import camera_status_manager

            # Prepare list of camera statuses
            camera_statuses = []
            
            # stream_dict values are now expected to be (camera_obj, stream_service) tuples
            # or None if not initialized. 
            # However, existing code might just store the service. 
            # We need to adapt based on how we decide to store it.
            # For now, let's assume we can fetch all cameras from DB to check them against the stream dict
            # BUT we don't have easy DB access here without a session.
            # 
            # Alternative: Iterate what we have in memory.
            # Let's inspect what's in CameraRepository.stream_dict
            
            for position, stream_entry in CameraRepository.stream_dict.items():
                status = "Offline"
                ip_address = "N/A"
                camera_id = 0
                serial_number = "N/A" # Default

                if stream_entry:
                     # If we change stream_dict to store (camera_obj, stream), accessing index 0 give us the model
                     try:
                        camera_obj = stream_entry[0]
                        if camera_obj:
                             status = "Online"
                             ip_address = camera_obj.ip_address
                             camera_id = camera_obj.id
                             # Assuming serial_number exists on the model, otherwise placeholder
                             # serial_number = getattr(camera_obj, 'serial_number', 'N/A') 
                     except:
                         pass

                # Check connection count on the stream service if available? 
                # Actually "Online" here means "Streaming Service is Running"
                
                if camera_id != 0:
                     camera_statuses.append({
                        "id": camera_id,
                        "position": position,
                        "ip_address": ip_address,
                        "status": status,
                        "serial_number": serial_number
                    })

            if camera_statuses:
                await camera_status_manager.send_json({
                    "type": "camera_status_update",
                    "data": camera_statuses
                })

        # Proper shutdown
        if GPU_AVAILABLE:
            nvmlShutdown()


class SystemMonitor:
    def __init__(self):
        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

    def collect(self):
        now = time.time()

        # -------- CPU --------
        cpu_percent = psutil.cpu_percent(interval=None)

        # -------- RAM --------
        mem = psutil.virtual_memory()

        # -------- DISK --------
        disk = psutil.disk_usage("/")

        # -------- NETWORK --------
        net = psutil.net_io_counters()
        elapsed = max(now - self.prev_time, 1e-6)

        upload_speed = (net.bytes_sent - self.prev_net.bytes_sent) / elapsed
        download_speed = (net.bytes_recv - self.prev_net.bytes_recv) / elapsed

        self.prev_net = net
        self.prev_time = now

        # -------- MULTI GPU --------
        gpu_data = []

        if GPU_AVAILABLE:
            for i in range(GPU_COUNT):
                try:
                    handle = nvmlDeviceGetHandleByIndex(i)

                    util = nvmlDeviceGetUtilizationRates(handle)
                    mem_info = nvmlDeviceGetMemoryInfo(handle)
                    temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

                    gpu_data.append({
                        "gpu_index": i,
                        "utilization_percent": util.gpu,
                        "memory_used_MB": mem_info.used / (1024 ** 2),
                        "memory_total_MB": mem_info.total / (1024 ** 2),
                        "temperature_C": temp,
                    })
                except Exception as e:
                    gpu_data.append({
                        "gpu_index": i,
                        "error": str(e)
                    })

        return {
            "cpu_percent": cpu_percent,
            "ram_percent": mem.percent,
            "disk_percent": disk.percent,
            "upload_MBps": upload_speed / (1024 ** 2),
            "download_MBps": download_speed / (1024 ** 2),
            "gpus": gpu_data if gpu_data else None,
            "carrier_turn_motor_status": CurrentInstanceRepositories.carrier_turn_motor_status or CurrentInstanceRepositories.cerrier_turn_motor_status,
            "cerrier_turn_motor_status": CurrentInstanceRepositories.carrier_turn_motor_status or CurrentInstanceRepositories.cerrier_turn_motor_status,
            "primer_box_turn_motor_status": CurrentInstanceRepositories.primer_box_turn_motor_status,
            "carrier_motor_status": CurrentInstanceRepositories.carrier_motor_status or CurrentInstanceRepositories.carrier_turn_motor_status or CurrentInstanceRepositories.cerrier_turn_motor_status,
            "fuze_motor_status": CurrentInstanceRepositories.fuze_motor_status or CurrentInstanceRepositories.primer_box_turn_motor_status,
            "box_motor_status": CurrentInstanceRepositories.box_motor_status or CurrentInstanceRepositories.primer_box_turn_motor_status,
        }

