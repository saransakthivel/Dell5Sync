import os
import time
import win32serviceutil
import win32service
import win32event
from subprocess import Popen, PIPE
import logging
from logging.handlers import RotatingFileHandler

# Logging setup 2

logging.basicConfig(level=logging.INFO)

log_directory = "C:\\Users\\admin\\OneDrive - E 4 Energy Solutions\\Saturn Pyro Files\\Documents\\Dell5Sync\\logs"
log_file = os.path.join(log_directory, "dramatiq_worker_service.log")

os.makedirs(log_directory, exist_ok=True)

log_handler = RotatingFileHandler(
    log_file, maxBytes=1 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)

logging.getLogger().addHandler(log_handler)


logging.info("Dell5 Dramatic Task Service: Initialization started.")

class TaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Dell5DramaticTaskService"  
    _svc_display_name_ = "Dell5 Dramatic Task Service"  
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
    
    def SvcStop(self):
        logging.info("Service is shutting down...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        logging.info("Service stopped successfully.")
        
        if self.process:
            self.process.terminate() 
            self.process.wait() 
    
    def SvcDoRun(self):
        logging.info("Service is now running.")
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        
        os.chdir("C:\\Users\\admin\\OneDrive - E 4 Energy Solutions\\Saturn Pyro Files\\Documents\\Dell5Sync")
        
        os.environ["MY_ENV_VAR"] = "value"
        try:
            logging.info("Starting Dramatiq worker process...")
            self.process = Popen(
                ['python', '-m', 'dramatiq', 'tasks'], 
                stdout=PIPE, 
                stderr=PIPE
            )
        except Exception as e:
            logging.error(f"Error starting Dramatiq worker: {str(e)}")
        
        while True:
            result = win32event.WaitForSingleObject(self.stop_event, 5000)  # 5 seconds check interval
            if result == win32event.WAIT_OBJECT_0:
                break

            output = self.process.stdout.read()
            if output:
                logging.info(f"Worker Output: {output.decode()}")

            error = self.process.stderr.read()
            if error:
                logging.error(f"Worker Error: {error.decode()}")

        self.process.terminate()
        logging.info("Dramatiq worker process terminated.")
        
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(TaskService)
