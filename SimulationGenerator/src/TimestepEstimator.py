#@brief Run many simulations of exponentially-decreasing time steps
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

from hydra import initialize, compose
from omegaconf import OmegaConf
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib
matplotlib.use("TkAgg")
import xarray as xr
import matplotlib.cm as cm

from src.RunASimulation import RunASimulation
from src.GeneralSimulationGeneration import GeneralSimulationGeneration



class TimestepEstimator(GeneralSimulationGeneration):
    
    def __init__ (self, config_folder, reference_config_file, configlist_file):
        super().__init__(config_folder, reference_config_file, configlist_file)
        return


    def generate_sim_configs(self, number_of_simulations, overwrite):
        print("Configuring parameters possible values before generating simulation configuration files...")
        #Assim temos certeza que o Ratio of calculation and output time steps is an integer
        next_timestep = self.param_cfg.time_step
        ts_list = [next_timestep]
        for i in range(1, number_of_simulations):
            next_timestep = (int)(self.param_cfg.output_time_step/2**i)
            self.param_cfg.time_step = next_timestep
            new_corrected_timestep = self.timestep_correction()

            ts_list.append((new_corrected_timestep))
        print("     * Time steps criados com sucesso...")


        sims_conf_folder = self.principal_cfg.paths.list_sim_configs_location
        os.makedirs(sims_conf_folder, exist_ok=True)
        relpath = os.path.join(sims_conf_folder, self.configlist_file)

        if os.path.exists(relpath):
                if overwrite:
                    print(f"     * Overwriting existing results folder {relpath}...")
                else:
                    raise FileExistsError(f"YAML configuration file '{relpath}' already exists. Select the overwrite option or rename the result folder.")
        
        print("\n")
        print("     * Creating all configuration files for simulations...")
        list_all_sims = []
        with initialize(config_path=self.config_folder, version_base=None):
            for idx, timestep in enumerate(ts_list):
                overrides = [
                    f"simulation_id={idx}",
                    f"time_step={timestep}",
                ]
                cfg_override = compose(config_name=self.principal_cfg.configs.base_sim_config, overrides=overrides) #self.principal_cfg.configs.base_sim_config is a string
                list_all_sims.append(cfg_override)
        OmegaConf.save(config = list_all_sims, f = relpath)
        print(f"      ... Lista de configurações criada com sucesso em {relpath}.")
        return


    @staticmethod
    def extrair_lat_lon(folder, number_of_simulations, particleidx = 0, dayslookahead = -1):
        """Extrai latitude e longitude do dia especificado de cada simulação."""
        latitudes = []
        longitudes = []

        # Loop em todos os resultados
        for i in range(number_of_simulations):
            arquivo_resultado = f"result_{i:04d}.nc"
            caminho = f"results/{folder}raw/{arquivo_resultado}"

            ds = xr.open_dataset(caminho, engine="netcdf4")
            
            lat_current = ds['lat'].values[particleidx] # For simulation i : [[ part1_day1, part1_day2, ...], [ part2_day1, part2_day2, ...], ...]
            lon_current = ds['lon'].values[particleidx]

            # Pega o último dia (ou duracao_dias se preferir)
            latitudes.append(lat_current[dayslookahead])
            longitudes.append(lon_current[dayslookahead])

            ds.close()

        return np.array(latitudes), np.array(longitudes) # At day i: [[ part1_ts1, part2_ts1, ...], [ part1_ts2, part2_ts2, ...], ...], each vector represents a timestep simulation


    @staticmethod
    def get_trajectory(folder, simulationidx=1, particleidx = 0):
        """Extrai toda a trajetória (lat/lon) de uma simulação específica."""
        arquivo_resultado = f"result_{simulationidx:04d}.nc"
        caminho = f"results/{folder}raw/{arquivo_resultado}"

        ds = xr.open_dataset(caminho, engine="netcdf4")
        lat_current = ds['lat'].values[particleidx] # For simulation i : [ partj_day1, partj_day2, ...]
        lon_current = ds['lon'].values[particleidx]
        ds.close()

        return lat_current, lon_current

    @staticmethod
    def measure_distance(lat1, lon1, lat2, lon2):
        """Compute great-circle distance(s) in meters — supports scalars or arrays."""
        R = 6378.137  # Radius of Earth in km
        dLat = np.radians(lat2 - lat1)
        dLon = np.radians(lon2 - lon1)

        a = (np.sin(dLat / 2)**2 +
            np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) *
            np.sin(dLon / 2)**2)

        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        d = R * c  # km
        return d * 1000  # meters


    def estimate_timestep(self, number_of_simulations, converging_tolerence, days_lookahead, particle_idx, simulation_idx, rk4flag, connect_final_points, compare_euler_rk4, timestep_folder, timestep_folder2):
        
        # Buscar os dados de simulação
        sims_conf_folder = self.principal_cfg.paths.list_sim_configs_location
        relpath = os.path.join(sims_conf_folder, self.configlist_file)
        sim_list = OmegaConf.load(relpath)
        ts_list = [sim["time_step"] for sim in sim_list]

        # Load initial datasets
        arquivo_resultado = RunASimulation.generate_result_fname(0, 0)
        try:
            ds_ref = xr.open_dataset(f"results/{timestep_folder}raw/" + arquivo_resultado, engine="netcdf4")
        except FileNotFoundError:
            print("O diretório contendo os resultados de simulações não existe. Verifique o nome do diretório, ou executa as simulações.")
            return
        lat_current = ds_ref['lat'].values # Simulation 0 : [[ part1_day1, part1_day2, ...], [ part2_day1, part2_day2, ...], ...]
        lon_current = ds_ref['lon'].values

        # Initialize arrays
        nb_days = lat_current.shape[1]
        err_array = np.full(lat_current.shape, np.inf)
        err_matrix = np.zeros((number_of_simulations, nb_days))
        err_atual = np.inf
        i = 1
        # Loop through timesteps
        print("-----------------------------------------")
        print(f"{'Time step (s)':>15} | {'Erro (m)':>10}")
        print("-----------------------------------------")
        best_timestep = np.inf
        convergiu = False
        while  (i < number_of_simulations): # and (err_atual >= eps_metre)?
            if not convergiu and (err_atual < converging_tolerence):
                best_timestep = ts_list[i]
                convergiu = True
                print(f"O timestep ótimo encontrado é {ts_list[i]} (s).")

            lat_ref = lat_current
            lon_ref = lon_current

            arquivo_resultado = f"result_{i:04d}.nc"
            try:
                ds_current = xr.open_dataset(f"results/{timestep_folder}raw/" + arquivo_resultado, engine="netcdf4")
            except FileNotFoundError:
                print(f"Arquivo 'result_{i:04d}.nc' não encontrado. Verifique o nome do diretório.")
                return
            lat_current = ds_current['lat'].values # For simulation i : [[ part1_day1, part1_day2, ...], [ part2_day1, part2_day2, ...], ...]
            lon_current = ds_current['lon'].values

            if lat_ref.shape != lat_current.shape or lon_ref.shape != lon_current.shape:
                print(f"Shape mismatch in file {arquivo_resultado}")
                i += 1
                continue

            err_array = TimestepEstimator.measure_distance(lat_ref, lon_ref, lat_current, lon_current)  # 2D-array (nb of particle, number of days)
            mean_array = err_array.mean(axis=0) #1D array
            err_matrix[i, :] = mean_array
            err_atual = mean_array[days_lookahead] # Média escalar varrendo todos os dias
            print(f"{ts_list[i]:>15} | {err_atual:>10.1f}")
            i += 1
        print("-----------------------------------------")

        if (i == number_of_simulations) and (err_atual > converging_tolerence):
            i -= 1
            print(f"Não atingiu convergência. O time step de {ts_list[i]} segundos não permitiu alcançar {converging_tolerence} metros de precisão.")
            best_timestep = ts_list[i]


        if compare_euler_rk4:
                # --- Plot lat/lon ---
                if rk4flag:
                    lat_rk4, lon_rk4 = TimestepEstimator.extrair_lat_lon(timestep_folder, number_of_simulations, particleidx = particle_idx, dayslookahead = days_lookahead)
                    try:
                        lat_euler, lon_euler = TimestepEstimator.extrair_lat_lon(timestep_folder2, number_of_simulations, particleidx = particle_idx, dayslookahead = days_lookahead)
                    except FileNotFoundError:
                        print("O diretório inserido para comparação não existe.")
                        return
                else:
                    lat_euler, lon_euler = TimestepEstimator.extrair_lat_lon(timestep_folder, number_of_simulations, particleidx = particle_idx, dayslookahead = days_lookahead)
                    try:
                        lat_rk4, lon_rk4 = TimestepEstimator.extrair_lat_lon(timestep_folder2, number_of_simulations, particleidx = particle_idx, dayslookahead = days_lookahead)
                    except FileNotFoundError:
                        print("O diretório inserido para comparação não existe.")
                        return
                    
                # --- Plotagem comparativa ---
                fig, axes = plt.subplots(1, 2, figsize=(12, 5), num="Euler vs RK4 Comparison")
                # Latitude
                ax = axes[0]
                ax.plot(ts_list, lat_euler, marker='o', color="#851717", label='Euler')
                ax.plot(ts_list, lat_rk4, marker='x', color="#172285", label='RK4')
                ax.set_xscale('log', base=2)
                ax.invert_xaxis()
                ax.xaxis.set_major_formatter(mticker.ScalarFormatter())  # decimal labels
                ax.xaxis.set_minor_formatter(mticker.NullFormatter())
                ax.set_xlabel("Time step (s)")
                ax.set_ylabel("Latitude (°)")
                ax.set_title(f"Evolução da latitude da partícula {particle_idx} no dia {days_lookahead}")
                ax.legend()
                ax.grid(True)

                # Longitude
                ax = axes[1]
                ax.plot(ts_list, lon_euler, marker='o', color="#851717", label='Euler')
                ax.plot(ts_list, lon_rk4, marker='x', color="#172285", label='RK4')
                ax.set_xscale('log', base=2)
                ax.invert_xaxis()
                ax.xaxis.set_major_formatter(mticker.ScalarFormatter())  # decimal labels
                ax.xaxis.set_minor_formatter(mticker.NullFormatter())
                ax.set_xlabel("Time step (s)")
                ax.set_ylabel("Longitude (°)")
                ax.set_title(f"Evolução da longitude da partícula {particle_idx} no dia {days_lookahead}")
                ax.legend()
                ax.grid(True)


                plt.tight_layout()
                plt.show()


                # --- Get trajectories ---

                if rk4flag:
                    lat_traj_rk4, lon_traj_rk4 = TimestepEstimator.get_trajectory(timestep_folder, simulationidx = simulation_idx, particleidx = particle_idx)
                    lat_traj_euler, lon_traj_euler = TimestepEstimator.get_trajectory(timestep_folder2, simulationidx = simulation_idx, particleidx = particle_idx)
                    lat_traj_final, lon_traj_final = TimestepEstimator.get_trajectory(timestep_folder2, simulationidx = number_of_simulations-1, particleidx = particle_idx)
                else:
                    lat_traj_euler, lon_traj_euler = TimestepEstimator.get_trajectory(timestep_folder, simulationidx = simulation_idx, particleidx = particle_idx)
                    lat_traj_rk4, lon_traj_rk4 = TimestepEstimator.get_trajectory(timestep_folder2, simulationidx = simulation_idx, particleidx = particle_idx)
                    lat_traj_final, lon_traj_final = TimestepEstimator.get_trajectory(timestep_folder, simulationidx = number_of_simulations-1, particleidx = particle_idx)

                # Plot the continuous trajectories
                plt.plot(lon_traj_euler, lat_traj_euler, '-x', color="#851717", label='Euler trajectory')
                plt.plot(lon_traj_rk4, lat_traj_rk4, '-x', color="#172285", label='RK4 trajectory')
                plt.plot(lon_traj_final, lat_traj_final, '--o', color='black', label='Finest trajectory (Euler)')
                # Highlight start and end
                plt.scatter(lon_traj_euler[0], lat_traj_euler[0], color="#851717", s=80, edgecolors='k')
                plt.scatter(lon_traj_rk4[0], lat_traj_rk4[0], color="#172285", s=80, edgecolors='k')
                plt.scatter(lon_traj_euler[-1], lat_traj_euler[-1], color="#851717", s=80)
                plt.scatter(lon_traj_rk4[-1], lat_traj_rk4[-1], color="#172285", s=80)
                plt.scatter(lon_traj_final[-1], lat_traj_final[-1], color="black", s=80)
                plt.xlabel("Longitude (°)")
                plt.ylabel("Latitude (°)")
                plt.title(f"Trajetória da partícula {particle_idx} (Δt = {ts_list[simulation_idx]} s)")
                plt.legend()
                plt.grid(True)
                plt.axis('equal')  # Keep aspect ratio consistent (1° lat ~ 1° lon visually)
                plt.tight_layout()
                plt.show()


        # --- Plot each time step trajectory --- 
        plt.figure(figsize=(8, 6))
        # Create colormap (red → yellow → green)
        cmap = cm.get_cmap('RdYlGn')
        colors = [cmap(i / (number_of_simulations - 1)) for i in range(number_of_simulations)]
        # Arrays para armazenar os pontos finais
        end_lats = []
        end_lons = []
        for simulationindex, color in zip(range(number_of_simulations), colors):
            lat_traj_rk4, lon_traj_rk4 = TimestepEstimator.get_trajectory(timestep_folder, simulationidx=simulationindex, particleidx=particle_idx)
            if not connect_final_points:
                plt.plot(lon_traj_rk4, lat_traj_rk4, '-x', color=color, alpha=0.8,
                        label=f'Δt = {ts_list[simulationindex]} s')
                # Mark start and end
                plt.scatter(lon_traj_rk4[0], lat_traj_rk4[0], color=color, s=40, edgecolors='k', zorder=3)
                plt.scatter(lon_traj_rk4[-1], lat_traj_rk4[-1], color=color, s=40, zorder=3)
                # Save endpoints for later connection
            end_lats.append(lat_traj_rk4[-1])
            end_lons.append(lon_traj_rk4[-1])
        # --- Connect all final points ---
        if connect_final_points:
            plt.plot(end_lons, end_lats, '--x', color='black', linewidth=1.5, markersize=5)
            plt.scatter(end_lons, end_lats, color=colors, s=50, zorder=4)

        # --- Formatting ---
        plt.xlabel("Longitude (°)")
        plt.ylabel("Latitude (°)")
        plt.title("Trajetórias RK4 — de Δt grande (vermelho) a pequeno (verde)")
        plt.grid(True)
        plt.axis('equal')
        plt.legend(
            title='Timestep (Δt)',
            loc='lower left',
            fontsize=8,
            title_fontsize=9
        )
        plt.tight_layout()
        plt.show()


        # --- Plot error evolution along time steps ---
        mean_error = np.nanmean(err_matrix[:, 1:], axis=1)
        max_error = np.nanmax(err_matrix[:, 1:], axis=1)
        min_error = np.nanmin(err_matrix[:, 1:], axis=1)

        plt.figure(figsize=(8,5))

        plt.plot(ts_list[1:], mean_error[1:], marker='o', color='#21908d', label='Mean error')
        plt.plot(ts_list[1:], max_error[1:], marker='x', color='#440154', alpha=0.9, label='Max error')
        plt.plot(ts_list[1:], min_error[1:], marker='x', color="#107c2b", alpha=0.9, label='Min error')


        plt.axhline(y=converging_tolerence, linestyle='--', color='#d62728', label='Tolerance')  # red

        plt.yscale('log')
        plt.xscale('log', base=2)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mticker.ScalarFormatter())  # decimal labels
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.invert_xaxis()
        plt.xlabel("Time step (s)")
        plt.ylabel("Error (m)")
        plt.title("Logarithmic evolution of error along simulation timesteps")
        plt.legend()
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()


        

        # --- Matrix threshold visualization / averaged error for a given time step at a given day ---
        
        # Evita log(0)
        err_matrix_pos = np.where(err_matrix > 0, err_matrix, np.nan)

        # Cria máscara: valores acima do threshold viram NaN
        #masked_matrix = np.where(err_matrix_pos <= eps_metre, err_matrix_pos, np.nan)

        # Cria colormap e define cor 'preta' para valores mascarados
        cmap = plt.cm.summer.copy()
        cmap.set_bad('black')

        plt.figure(figsize=(12, 6))
        plt.imshow(
            np.log(err_matrix),
            aspect='auto',
            cmap=cmap,
            interpolation='none'
        )
        plt.colorbar(label='Log da distância (m)')
        plt.xlabel('Dias')
        plt.ylabel('Índice do time step')
        plt.title(f'Diferença (m) da partícula com o timestep anterior (valores > {converging_tolerence} m em preto)')
        plt.tight_layout()
        plt.show()

        
        # Calculo do número de Courant associado a este time step
        arquivo_resultado = f"result_{(number_of_simulations-1):04d}.nc" # Buscando a simulação com o melhor timestep
        ds_current = xr.open_dataset(f"results/{timestep_folder}raw/" + arquivo_resultado, engine="netcdf4") # Carregando os resultados

        seax = max(ds_current['x_sea_water_velocity'].values[0]) #Velocidade da correnteza na direção horizontal no dia 4 (u_x)
        seay = max(ds_current['y_sea_water_velocity'].values[0])
        windx = max(ds_current['x_wind'].values[0]) #Velocidade do maior vento na direção horizontal  (u_x)
        windy = max(ds_current['y_wind'].values[0]) #Vento na direção vertical (u_y)

        position_lat = ds_current['lat'].values[0][0] # Posição aproximada na surface do globo, considerando uma partícula dada em um instante dado
        position_lon = ds_current['lon'].values[0][0]
        resolucao_espacial_lon = 0.083
        resolucao_espacial_lat = 0.083
        distx = TimestepEstimator.measure_distance(position_lat, position_lon, position_lat, position_lon+resolucao_espacial_lon) #Distância percorrida na direção longitudinal/horizontal
        disty = TimestepEstimator.measure_distance(position_lat, position_lon, position_lat+resolucao_espacial_lat, position_lon) #Distância percorrida na direção latitudinal/vertical

        Cx = (seax + 0.03*windx) * best_timestep / distx # ux*deltax / deltat
        Cy = (seay + 0.03*windy) * best_timestep / disty # uy*deltay / deltat


        print("\n\033[1;36m==== RESULTADOS ====\033[0m")
        print(f"Maior velocidade de vento horizontal (m/s)      :   \033[1m{windx:.3f}\033[0m")
        print(f"Maior velocidade de vento vertical (m/s)        :   \033[1m{windy:.3f}\033[0m")
        print(f"Maior velocidade de correnteza horizontal       :   \033[1m{seax:.3f}\033[0m")
        print(f"Maior velocidade de correnteza vertical         :   \033[1m{seay:.3f}\033[0m")
        print(f"Tamanho horizontal de uma célula (m)            :   \033[1m{distx:.1f}\033[0m")
        print(f"Tamanho vertical de uma célula (m)              :   \033[1m{disty:.1f}\033[0m")
        print(f"Coeficiente de Courant horizontal Cx (s.d.)     :   \033[1m{Cx}\033[0m")
        print(f"Coeficiente de Courant vertical Cy (s.d.)       :   \033[1m{Cy}\033[0m")
        print("\033[1;36m===============================\n\033[0m")

        return