#@brief Parent class for displaying components with Tkinter
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

from abc import abstractmethod
from typing import final
import tkinter as tk
import os 
from tkinter import messagebox
from hydra import initialize, compose

class DisplayActions:

    @staticmethod
    @final
    def clear(master_root: tk.Tk):
        # Clear any existing widgets
        for widget in master_root.winfo_children():
            widget.destroy()


    @staticmethod
    @abstractmethod
    def execute_button(config_folder: str, parameters: list):
        pass 


    @staticmethod
    @abstractmethod
    def gui_display(entry_inputfolder: tk.Entry, root: tk.Tk, go_back_callback):
        pass


    @staticmethod
    def config_files_exist(config_folder: str):

        # ------------------- VERIFICACAO ANTES DE ENTRAR EFETIVAMENTE -------------------
        if not os.path.exists(config_folder):
            messagebox.showerror(
                "Erro",
                "O diretório inserido que deve conter as configurações não existe."
            )
            return
        elif not os.path.exists(os.path.join(config_folder, "main.yaml")):
            messagebox.showerror(
                "Erro",
                "O arquivo main não existe dentro do arquivo"
            )
            return
        else:
            with initialize(config_path=f"../{config_folder}", version_base=None): # Necessary since these GUI functions are not at the same level than the conf/ folder
                principal_cfg = compose(config_name="main")
                cm_configfile_path = os.path.join(config_folder, principal_cfg.configs.cm_config)
                gif_configfile_path = os.path.join(config_folder, principal_cfg.configs.gif_config)
                credentials_configfile_path = os.path.join(config_folder, principal_cfg.configs.cm_login)
            if not os.path.exists(f"{cm_configfile_path}.yaml"):
                messagebox.showerror(
                    "Erro",
                    f"O arquivo de configuração {cm_configfile_path}.yaml não existe.\n Ele é necessário para recuperar do Copernicus Marine dados de vento e correnteza.\nVerifique a existência e o nome inserido no arquivo main.YAML"
                )
            elif not os.path.exists(f"{gif_configfile_path}.yaml"):
                messagebox.showerror(
                    "Erro",
                    f"O arquivo de configuração {gif_configfile_path}.yaml não existe.\n Ele é necessário para parametrizar as animações GIF.\nVerifique a existência e o nome inserido no arquivo main.YAML"
                )
            elif not os.path.exists(f"{credentials_configfile_path}.yaml"):
                messagebox.showerror(
                    "Erro",
                    f"O arquivo de configuração {credentials_configfile_path}.yaml não existe.\n Ele é necessário para fazer o login no Copernicus Marine.\nVerifique a existência e o nome inserido no arquivo main.YAML"
                )
            else:
                print("[Timestep Estimator] - Arquivos de configuração encontrados! Aguarde...")
                return True
        return False