class _Config:
    # Monitor GL objects and emit a warning whenever one is garbage collected without being
    # destroyed first.
    monitor_leaks: bool = False

    def development_mode(self):
        """Enable configuration presets for development."""
        self.monitor_leaks = True

    def production_mode(self):
        """Enable configuration presets for production."""
        self.monitor_leaks = False


# Global configuration object for Glip.
cfg = _Config()
