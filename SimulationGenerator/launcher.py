#@brief Script to launch the application
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

import tkinter as tk
from gui.SimGenGUI import SimGenGUI
from gui.TimestepEstimatorGUI import TimestepEstimatorGUI
from gui.DisplayActions import DisplayActions


class Launcher:
    def __init__(self):
        self.master_root = tk.Tk()

    def clear(self):
        for widget in self.master_root.winfo_children():
            widget.destroy()

    def show_home(self):
        DisplayActions.clear(self.master_root)

        self.master_root.title("Bem-vindo ao gerador de simulações Opendrift")
        self.master_root.geometry("450x1020")

        lbl_inputfolder = tk.Label(self.master_root, text="Insira o diretório que contém os arquivos de configuração:") 
        lbl_inputfolder.pack(fill="x")

        entry_inputfolder = tk.Entry(self.master_root)
        entry_inputfolder.pack(fill="x", pady=3)
        entry_inputfolder.insert(0, "conf/")

        label = tk.Label(self.master_root, text="Escolha uma das opções seguintes", font=("Arial", 12))
        label.pack(pady=20)

        btn_sim = tk.Button(
            self.master_root, text="Simulation Generator",
            command=lambda: SimGenGUI.gui_display(entry_inputfolder, self.master_root, self.show_home)
        )
        btn_sim.pack(pady=10)

        btn_te = tk.Button(
            self.master_root, text="Timestep Estimator",
            command=lambda: TimestepEstimatorGUI.gui_display(entry_inputfolder, self.master_root, self.show_home)
        )
        btn_te.pack(pady=10)

    def run(self):
        self.show_home()
        self.master_root.mainloop()
    
if __name__ == "__main__":
    L = Launcher()
    L.run()