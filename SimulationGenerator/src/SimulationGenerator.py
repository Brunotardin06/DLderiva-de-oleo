#@brief Run many simulations given various non-fixed parameters
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

from hydra import initialize, compose
from omegaconf import OmegaConf
import os
from datetime import datetime, timedelta
from itertools import product
import numpy as np

from src.GeneralSimulationGeneration import GeneralSimulationGeneration

class SimulationGenerator(GeneralSimulationGeneration):

    def __init__ (self, config_folder, reference_config_file, configlist_file):
        super().__init__(config_folder, reference_config_file, configlist_file)
        return


    def generate_sim_configs(self, overwrite):
        sims_conf_folder = self.principal_cfg.paths.list_sim_configs_location
        os.makedirs(sims_conf_folder, exist_ok=True)
        relpath = os.path.join(sims_conf_folder, self.configlist_file)

        if os.path.exists(relpath):
                if overwrite:
                    print(f"Overwriting existing results folder {relpath}.")
                else:
                    raise FileExistsError(f"YAML configuration file '{relpath}' already exists. Select the overwrite option or rename the result folder.")

        ### CUSTOMIZATION OF CONFIGURATION FILES TO BE GENERATED ###
        print("\n")
        print(f"Configuring parameters list of values before generating simulation configuration files...")

        # Time step correction
        time_step__corrected = self.timestep_correction()

        #Start dates
        start_date_base = datetime.strptime(self.param_cfg.start_date, "%Y-%m-%d")
        start_date_list = [start_date_base + timedelta(days=i) for i in range(0, self.param_cfg.nb_time_slots*self.param_cfg.duration_days, self.param_cfg.duration_days)]
        print(f"  *  {self.param_cfg.nb_time_slots} time ranges of {self.param_cfg.duration_days} days each have been configured.")


        #Longitude and latitude position of the randomly-chosen oil spill centers
        media_lon =  (self.gif_cfg.min_lon+self.gif_cfg.max_lon)/2 # center longitude of the frame
        media_lat =  (self.gif_cfg.min_lat+self.gif_cfg.max_lat)/2 # center latitude of the frame
        range_lon = (self.gif_cfg.min_lon-self.gif_cfg.max_lon)*self.param_cfg.constrain_rate # dentro de um quadro de tamanho de 50% do quadro inteiro
        range_lat = (self.gif_cfg.min_lat-self.gif_cfg.max_lat)*self.param_cfg.constrain_rate # dentro de um quadro de tamanho de 50% do quadro inteiro
        spill_lons = []
        spill_lats = []
        for _ in range(self.param_cfg.n_diff_center_spill_pos):
            spill_lons.append(media_lon+np.random.uniform(-range_lon/2, range_lon/2))
            spill_lats.append(media_lat+np.random.uniform(-range_lat/2, range_lat/2))
        print(f"  *  {self.param_cfg.n_diff_center_spill_pos} spill center positions randomly chosen between longitude range [{media_lon-range_lon/2}, {media_lon+range_lon/2}] and latitude range [{media_lat-range_lat/2}, {media_lat+range_lat/2}].")
        
        #Radius values
        print(f"  *  {len(self.param_cfg.spill_radius)} spill center radiuses manually chosen.")
        combinations = list(product(start_date_list, spill_lons, spill_lats, self.param_cfg.spill_radius))


        print("\n")
        print("Creating all configuration files for simulations...")
        list_sims = []
        with initialize(config_path=self.config_folder, version_base=None):
            for idx, (start_date, lon, lat, radius) in enumerate(combinations):
                overrides = [
                    f"simulation_id={idx}",
                    f"start_date={start_date.strftime('%Y-%m-%d')}",
                    f"end_date={(start_date + timedelta(days=self.param_cfg.duration_days)).strftime('%Y-%m-%d')}",
                    f"spill_lon={lon}",
                    f"spill_lat={lat}",
                    f"spill_radius={radius}",
                    f"time_step={time_step__corrected}"
                ]
                cfg_override = compose(config_name=self.principal_cfg.configs.base_sim_config, overrides=overrides)
                list_sims.append(cfg_override)

        print("Saving YAML file...")
        OmegaConf.save(config = list_sims, f = relpath)
        print(f"{len(spill_lons)} x {len(spill_lats)} x {len(self.param_cfg.spill_radius)} x {len(start_date_list)} = {len(combinations)} arquivos de configuração gerados em '{relpath}'.")
        return