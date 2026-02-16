"""
Lightning AI App Configuration for Boltz-2 Structure Prediction
This file enables deployment on Lightning AI Studios
"""

import lightning as L
from lightning.app.components import LightningFlow
import subprocess
import os


class Boltz2App(LightningFlow):
    """Lightning Flow for Boltz-2 Gradio App"""
    
    def __init__(self):
        super().__init__()
        self.ready = False
    
    def run(self):
        # Install dependencies if needed
        if not self.ready:
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
            self.ready = True
        
        # Launch Gradio app
        subprocess.run(["python", "app.py"], check=True)


class RootFlow(L.LightningFlow):
    """Root flow for Lightning AI deployment"""
    
    def __init__(self):
        super().__init__()
        self.boltz_app = Boltz2App()
    
    def run(self):
        self.boltz_app.run()
    
    def configure_layout(self):
        return [
            {"name": "Boltz-2 Structure Prediction", "content": self.boltz_app}
        ]


# For direct Lightning AI deployment
app = L.LightningApp(RootFlow())
