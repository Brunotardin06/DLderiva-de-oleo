#@brief Specific class to show modifyable parameters for simulation generation
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

from omegaconf import OmegaConf
import os
import tkinter as tk

from src.SimulationGenerator import SimulationGenerator
from gui.DisplayActions import DisplayActions
from exceptions.CustomExceptions import DownloadEnvironmentDataError, ConfigFileNotFound, TimestepOverOutputTimestep, CopernicusDateRangeError

class SimGenGUI(DisplayActions):


    def execute_button(config_folder, parameters):
        try:
            outros_params = parameters[1]

            # Save YAML file into *configfolder*/reference_sim_config.yaml
            ref_config_name = "reference_simgen_config"
            output_yaml = os.path.join(config_folder, ref_config_name + ".yaml")
            reference_simconfig = OmegaConf.create(parameters[0])
            OmegaConf.save(config=reference_simconfig, f=output_yaml)

            SG = SimulationGenerator(config_folder, ref_config_name, outros_params["config_fname"])
            SG.generate_sim_configs(outros_params["overwrite"])
            if outros_params["run_simulations"]:
                SG.set_result_folder(outros_params["resultfolder"])
                SG.generate_simulations(outros_params["workers"], outros_params["verbose"], outros_params["rk4flag"], outros_params["overwrite"])
            else:
                print("Execução das simulações não foi ativada")
            print("Programa terminado!")


        except FileExistsError as e:
            print(f"Error: {e}")

        except FileNotFoundError as e:
            print(f"Error: {e}")

        except DownloadEnvironmentDataError as e:
            print(f"Error: {e}")

        except ConfigFileNotFound as e:
            print(f"Error: {e}")

        except TimestepOverOutputTimestep as e:
            print(f"Error: {e}")
        
        except CopernicusDateRangeError as e:
            print(f"Error: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")


    def gui_display(entry_inputfolder: tk.Entry, root: tk.Tk, go_back_callback):
        configfolder = entry_inputfolder.get().strip()
        if not DisplayActions.config_files_exist(configfolder):
            return

        DisplayActions.clear(root)

        # ------------------- Tkinter GUI -------------------

        frame = tk.Frame(root)
        frame.pack(pady=5)

        def add_field(frame, label, default):
            lbl = tk.Label(frame, text=label, anchor="w")
            lbl.pack(fill="x")
            entry = tk.Entry(frame)
            entry.insert(0, str(default))
            entry.pack(fill="x", pady=3)
            return entry
        
        entry_workers = add_field(frame, "Número de workers (simulação):", 4)

        # ---------------- SIMULATION PARAMETERS SECTION ----------------
        params_frame = tk.LabelFrame(root, text="Parâmetros da Simulação", font=("Arial", 9, "bold"))
        params_frame.pack(fill="x", pady=10, padx=10)

        entry_start_date     = add_field(params_frame, "Data início (YYYY-MM-DD):", "2023-05-01")
        entry_duration_days  = add_field(params_frame, "Duração (dias):", 5)
        entry_nb_time_slots  = add_field(params_frame, "Número de time slots:", 5)
        entry_spill_radius   = add_field(params_frame, "Raio do spill (ex: 4000,7000):", "4000,7000")
        entry_n_diff_center  = add_field(params_frame, "Número de centros:", 2)
        entry_constrain_rate = add_field(params_frame, "Constrain rate:", 0.5)
        entry_num_seed       = add_field(params_frame, "Num. partículas seed:", 1000)
        entry_time_step      = add_field(params_frame, "Time step (s):", 180)
        entry_output_step    = add_field(params_frame, "Output time step (s):", 86400)

        # Checkboxes to select when simulation running is checked
        var_runsims = tk.BooleanVar(value=False)
        var_verbose = tk.BooleanVar(value=False)
        var_overwrite = tk.BooleanVar(value=False)
        var_rk4 = tk.BooleanVar(value=True)
        cb_runsims = tk.Checkbutton(root, text="Rodar simulações", variable=var_runsims)
        cb_overwrite = tk.Checkbutton(root, text="Overwrite already existing config/result files", variable=var_overwrite)
        cb_verbose   = tk.Checkbutton(root, text="Verbose da simulação", variable=var_verbose)
        cb_rk4     = tk.Checkbutton(root, text="Usar Runge-Kutta 4", variable=var_rk4)


        lbl_outputconfig = tk.Label(frame, text="Output config file (.yaml):")
        lbl_outputconfig.pack(fill="x")
        entry_configlist = tk.Entry(frame)
        entry_configlist.pack(fill="x", pady=3)

        lbl_folder = tk.Label(frame, text="Folder para armazenar os resultados (termina com '/'):")
        lbl_folder.pack(fill="x")
        entry_resultfolder = tk.Entry(frame)
        entry_resultfolder.pack(fill="x", pady=3)


        entry_configlist.delete(0, tk.END)
        entry_configlist.insert(0, "default_simulations_configs_list.yaml")
        entry_resultfolder.delete(0, tk.END)
        entry_resultfolder.insert(0, "default_generation_folder/")

        def update_folder_state(*args):
            if var_runsims.get():
                entry_workers.config(state="normal")
                cb_verbose.config(state="normal")
                cb_verbose.update()

                entry_resultfolder.config(state="normal")

                cb_rk4.config(state="normal")
                cb_rk4.update()
            else:
                entry_workers.config(state="disabled")
                cb_verbose.config(state="disabled")
                var_verbose.set(False)
                entry_resultfolder.config(state="disabled")
                cb_rk4.config(state="disabled")
                var_rk4.set(False)
            var_runsims.trace("w", update_folder_state)
        update_folder_state()

        cb_runsims.pack(pady=20)
        cb_overwrite.pack(pady=20)
        cb_verbose.pack(anchor="w", padx=20)
        cb_rk4.pack(anchor="w", padx=20)



        #Go Back Button
        btn_back = tk.Button(root, text="Voltar", 
                        command=go_back_callback,
                        bg="#ff6347", fg="white")
        btn_back.pack(pady=10, ipadx=10, ipady=5)

        # Run button
        btn_run = tk.Button(
            root,
            text="Executar",
            bg="#1e90ff", fg="white",
            command=lambda: SimGenGUI.execute_button(
                configfolder,
                [
                    {
                        "simulation_id": 0,
                        "start_date": entry_start_date.get().strip(),
                        "end_date": entry_start_date.get().strip(),  # By default
                        "min_lon": -46.0,
                        "max_lon": -37.0,
                        "min_lat": -27.0,
                        "max_lat": -21.0,
                        "duration_days": int(entry_duration_days.get()),
                        "nb_time_slots": int(entry_nb_time_slots.get()),
                        "spill_lon": -39.0,
                        "spill_lat": -25.0,
                        "spill_radius": [float(v) for v in entry_spill_radius.get().split(",")],
                        "n_diff_center_spill_pos": int(entry_n_diff_center.get()),
                        "constrain_rate": float(entry_constrain_rate.get()),
                        "num_seed_elements": int(entry_num_seed.get()),
                        "time_step": int(entry_time_step.get()),
                        "output_time_step": int(entry_output_step.get()),
                    },
                    {
                        "run_simulations": bool(var_runsims.get()),
                        "verbose": bool(var_verbose.get()),
                        "rk4flag": bool(var_rk4.get()),
                        "workers": int(entry_workers.get()),
                        "configfolder": configfolder,
                        "resultfolder": entry_resultfolder.get().strip(),
                        "config_fname": entry_configlist.get().strip(),
                        "overwrite": bool(var_overwrite.get()),
                    },
                ]
            )
        )
        btn_run.pack(pady=10, ipadx=10, ipady=5)