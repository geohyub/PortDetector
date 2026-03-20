"""Worker lifecycle manager."""


class Scheduler:
    def __init__(self, ping_worker, scan_worker, interface_worker):
        self.ping_worker = ping_worker
        self.scan_worker = scan_worker
        self.interface_worker = interface_worker

    def start_all(self, ping_interval=5, interface_interval=3):
        self.ping_worker.start(interval=ping_interval)
        self.interface_worker.start(interval=interface_interval)

    def stop_all(self):
        self.ping_worker.stop()
        self.interface_worker.stop()

    def restart_ping(self, interval=None):
        self.ping_worker.stop()
        if interval:
            self.ping_worker.start(interval=interval)
        else:
            self.ping_worker.start()

    def restart_interface(self, interval=None):
        self.interface_worker.stop()
        if interval:
            self.interface_worker.start(interval=interval)
        else:
            self.interface_worker.start()
