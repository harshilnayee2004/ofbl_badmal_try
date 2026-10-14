import logging
from repositories.camera_repositories import CameraRepository
from threading import Thread


class StreamManager:
    

    @staticmethod
    def start_all_streams():
        for position, obj in CameraRepository.stream_dict.items():
            logging.info("Searching for cameras")
            if obj is not None:
                logging.info("found camera")
                Thread(target=obj.start, daemon=True).start()
                
    @staticmethod
    def stop_all_streams():
        for position, obj in CameraRepository.stream_dict.items():
            if obj is not None:
                obj.stop()

    @staticmethod
    def restart_stream(position:str):
        if position in CameraRepository.stream_dict:
            if CameraRepository.stream_dict[position] is not None:
                CameraRepository.stream_dict[position].stop()
                CameraRepository.stream_dict[position].start()