#@brief Specific class to show modifiable parameters time step analysis
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025


from omegaconf import OmegaConf
import os

import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")

from src.TimestepEstimator import TimestepEstimator
from gui.DisplayActions import DisplayActions
from exceptions.CustomExceptions import DownloadEnvironmentDataError, ConfigFileNotFound, TimestepOverOutputTimestep, CopernicusDateRangeError


'''
Essa aplicação tem como objetivo estimar o valor do time step que permite uma convergência dos resultados obtidos pelos esquemas de integração numérica 
Ela é feita de dois passos: a geração de simulações - que o usuário pode pular utilizando o parâmetro apropriado - e o desenho de gráficos assim como a exibição dos resultados no console.
'''

class TimestepEstimatorGUI(DisplayActions):


    def execute_button(config_folder, parameters):
        try:
            outros_params = parameters[1]

            # Save YAML file into *configfolder*/reference_sim_config.yaml
            ref_config_name = "reference_tsestimator_config"
            output_yaml = os.path.join(config_folder, ref_config_name + ".yaml")
            reference_simconfig = OmegaConf.create(parameters[0])
            OmegaConf.save(config=reference_simconfig, f=output_yaml)

            TE = TimestepEstimator(config_folder, ref_config_name, outros_params["config_fname"])
            TE.generate_sim_configs(outros_params["number_of_simulations"], outros_params["overwrite"])
            if outros_params["run_simulations"]:
                TE.set_result_folder(outros_params["result_folder"])
                TE.generate_simulations(outros_params["workers"], outros_params["verbose"], outros_params["rk4flag"], outros_params["overwrite"])
            else:
                print("Execução das simulações não foi ativada")
            TE.estimate_timestep(outros_params["number_of_simulations"], outros_params["tolerancia"], outros_params["days_lookahead"], outros_params["particle_number"], outros_params["simulation_number"], outros_params["rk4flag"],  outros_params["connect_final_points"], outros_params["compare_euler_rk4"], outros_params["result_folder"] , outros_params["comparison_result_folder"])
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


    def gui_display(entry_inputfolder: tk.Entry, root: tk, go_back_callback):
        configfolder = entry_inputfolder.get().strip()
        if not DisplayActions.config_files_exist(configfolder):
            return

        DisplayActions.clear(root)

        # -----------------------
        # Tkinter Window Setup
        # -----------------------

        frame = tk.Frame(root)
        frame.pack(pady=5)

        main_frame = tk.Frame(root)
        main_frame.pack(pady=5, fill="x")

        def add_field(parent, label, default):
            lbl = tk.Label(parent, text=label, anchor="w")
            lbl.pack(fill="x")
            entry = tk.Entry(parent)
            entry.insert(0, str(default))
            entry.pack(fill="x", pady=3)
            return entry

        # ---------------- SIMULAÇÃO SECTION ----------------
        sim_frame = tk.LabelFrame(main_frame, text="Simulação", font=("Arial", 9, "bold"))
        sim_frame.pack(fill="x", pady=10)

        entry_time_step = add_field(sim_frame, "Time step inicial (s):", 86400)
        entry_nsim = add_field(sim_frame, "Número de simulações (necessário quanto para simulação como para visualização):", 15)
        entry_workers = add_field(sim_frame, "Número de workers (multiprocessamento):", 4)

        # ---------------- VISUALIZAÇÃO SECTION ----------------
        vis_frame = tk.LabelFrame(main_frame, text="Visualização gráfica", font=("Arial", 9, "bold"))
        vis_frame.pack(fill="x", pady=10)

        entry_tol = add_field(vis_frame, "Tolerância (m):", 100)
        entry_days = add_field(vis_frame, "Quantos dias para frente:", 9)
        entry_pid = add_field(vis_frame, "Índice da partícula:", 7)
        entry_sid = add_field(vis_frame, "Índice da simulação:", 8)

        

        # Checkboxes to select when simulation running is checked
        var_runsims = tk.BooleanVar(value=False)
        var_verbose = tk.BooleanVar(value=False)
        var_compare = tk.BooleanVar(value=False)
        var_overwrite = tk.BooleanVar(value=False)
        var_rk4 = tk.BooleanVar(value=False)
        var_connect = tk.BooleanVar(value=False)

        cb_runsims   = tk.Checkbutton(root, text="Rodar simulações", variable=var_runsims)
        #cb_rerunall   = tk.Checkbutton(root, text="Reexecutar todas (obrigatório quando nada existe)", variable=var_rerunall)
        cb_verbose   = tk.Checkbutton(root, text="Verbose da simulação", variable=var_verbose)
        cb_compare = tk.Checkbutton(root, text="Comparar Euler vs RK4", variable=var_compare)
        cb_overwrite = tk.Checkbutton(root, text="Overwrite already existing config/result files", variable=var_overwrite)
        cb_rk4     = tk.Checkbutton(root, text="Usar Runge-Kutta 4", variable=var_rk4)
        cb_connect     = tk.Checkbutton(root, text="Conectar os pontos finais", variable=var_connect)

        cb_runsims.pack(anchor="w", padx=20)
        cb_overwrite.pack(anchor="w", padx=20)
        cb_verbose.pack(anchor="w", padx=20)
        cb_compare.pack(anchor="w", padx=20)
        cb_rk4.pack(anchor="w", padx=20)
        cb_connect.pack(anchor="w", padx=20)

        lbl_outputconfig = tk.Label(frame, text="YAML filename in which the configs of simulation are stored")
        lbl_outputconfig.pack(fill="x")
        entry_configlist = tk.Entry(frame)
        entry_configlist.pack(fill="x", pady=3)

        lbl_folder1 = tk.Label(frame, text="Folder das simulações (termina com '/'):")
        lbl_folder1.pack(fill="x")
        entry_folder1 = tk.Entry(frame)
        entry_folder1.pack(fill="x", pady=3)

        lbl_folder2 = tk.Label(frame, text="Folder para comparação gráfica:")
        lbl_folder2.pack(fill="x")
        entry_folder2 = tk.Entry(frame)
        entry_folder2.pack(fill="x", pady=3)


        entry_folder1.delete(0, tk.END)
        entry_folder1.insert(0, "default_timesteps_rk4/")
        entry_folder2.delete(0, tk.END)
        entry_folder2.insert(0, "default_timesteps_euler/")
        entry_configlist.delete(0, tk.END)
        entry_configlist.insert(0, "default_timesteps_sim_configs_list.yaml")


        def update_runsims_state(*args):
            if var_runsims.get():
                cb_rk4.config(state="normal")
                cb_verbose.config(state="normal")
                entry_workers.config(state="normal")
                entry_time_step.config(state="normal")
            else:
                cb_rk4.config(state="disabled")
                var_rk4.set(False)
                cb_verbose.config(state="disabled")
                var_verbose.set(False)
                entry_workers.config(state="disabled")
                entry_time_step.config(state="disabled")
        var_runsims.trace("w", update_runsims_state)
        update_runsims_state()


        def update_folder2_state(*args):
            if var_compare.get():
                entry_folder2.config(state="normal")
                entry_sid.config(state="normal")
            else:
                entry_folder2.config(state="disabled")
                entry_sid.config(state="disabled")
        var_compare.trace("w", update_folder2_state)
        update_folder2_state()


        # Go Back Button
        btn_back = tk.Button(root, text="Voltar", 
                        command=go_back_callback,
                        bg="#ff6347", fg="white")
        btn_back.pack(pady=10, ipadx=10, ipady=5)

        # Run button
        btn_run = tk.Button(
            root,
            text="Executar",
            bg="#1e90ff", fg="white",
            command=lambda: TimestepEstimatorGUI.execute_button(
                configfolder,
                [
                    {
                        "simulation_id": 0,
                        "start_date": "2023-05-01",
                        "end_date": "2023-05-10",  # By default
                        "min_lon": -46.0,
                        "max_lon": -37.0,
                        "min_lat": -27.0,
                        "max_lat": -21.0,
                        "spill_lon": -39.0,
                        "spill_lat": -25.0,
                        "spill_radius": 6000.0,
                        "num_seed_elements": 100,
                        "time_step": int(entry_time_step.get()),
                        "output_time_step": 86400,
                    },
                    {
                        "run_simulations": bool(var_runsims.get()),
                        "number_of_simulations": int(entry_nsim.get()),
                        "tolerancia": float(entry_tol.get()), 
                        "days_lookahead": int(entry_days.get()), 
                        "particle_number": int(entry_pid.get()),
                        "simulation_number": int(entry_sid.get()), 
                        "verbose": bool(var_verbose.get()),
                        "rk4flag": bool(var_rk4.get()),
                        "workers": int(entry_workers.get()),
                        "result_folder": entry_folder1.get().strip(),
                        "comparison_result_folder": entry_folder2.get().strip(),
                        "config_fname": entry_configlist.get().strip(),
                        "connect_final_points": bool(var_connect.get()),
                        "compare_euler_rk4": bool(var_compare.get()),
                        "overwrite": bool(var_overwrite.get()),
                    },
                ]
            )
        )
        btn_run.pack(pady=10, ipadx=10, ipady=5)