#@brief Run one simulation using Opendrift
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

import os

from opendrift.models.oceandrift import OceanDrift
from opendrift.models.openoil import OpenOil
from opendrift.readers import reader_netCDF_CF_generic # Leitor de dados NetCDF/OPeNDAP

from omegaconf import DictConfig
from src.Fetch import Fetch
from datetime import datetime

from hydra import initialize, compose
from exceptions.CustomExceptions import CopernicusDateRangeError

class RunASimulation:

    def __init__(self, config_folder: str, main_cfg: DictConfig):
        with initialize(config_path=config_folder, version_base=None):
            self.cm_data = compose(config_name=main_cfg.configs.cm_config) # DictConfig
            self.gif_config = compose(config_name=main_cfg.configs.gif_config) # DictConfig
            self.credentials = compose(config_name=main_cfg.configs.cm_login) # DictConfig
            self.sim_cfg_file = compose(config_name=main_cfg.configs.base_sim_config) # DictConfig
        self.result_path = main_cfg.paths.sim_results_location # str



    def set_sim_config_file(self, sim_cfg_file: DictConfig):
        self.sim_cfg_file = sim_cfg_file


    @staticmethod
    def generate_result_fname(id: int, extension: int):
        if extension == 0:
            return f"result_{id:04d}.nc"
        else:
            return f"result_{id:04d}.gif"
    

    def run_simulation(self, verbose, rk4):

        if ((self.sim_cfg_file.start_date < self.cm_data.start_date) or (self.sim_cfg_file.end_date > self.cm_data.end_date)):
            raise CopernicusDateRangeError(f"The imported Copernicus Marine environment data doesn't contain the simulation date range.")
        
        print(f"\n{self.sim_cfg_file.simulation_id+1}a simulação iniciada ...")


        os.makedirs(self.result_path, exist_ok=True)

        o = OpenOil(loglevel=20 if verbose else 50)

        ############## FETCH DATA ##############
        F = Fetch(self.cm_data, self.credentials)
        current_fname = F.GetCurrentFileName(with_folder = True)
        if not os.path.exists(current_fname):
            print(f"run_simulation: o current path {current_fname} não existe.")
            return
        
        wind_fname = F.GetWindFileName(with_folder = True)
        if not os.path.exists(wind_fname):
            print(f"run_simulation: o wind path {wind_fname} não existe.")
            return
        

        ############## ADD READERS ##############
        
        reader_current = reader_netCDF_CF_generic.Reader(current_fname)
        reader_wind    = reader_netCDF_CF_generic.Reader(wind_fname)
        o.add_reader([reader_current, reader_wind])

        if verbose:
            print('Current Reader details:\n')
            print(reader_current)

            print('Wind Reader details:\n')
            print(reader_wind)

        # Desativa particulas fora do dominio
        o.set_config('drift:deactivate_west_of' , self.sim_cfg_file.min_lon)
        o.set_config('drift:deactivate_east_of' , self.sim_cfg_file.max_lon)
        o.set_config('drift:deactivate_south_of', self.sim_cfg_file.min_lat)
        o.set_config('drift:deactivate_north_of', self.sim_cfg_file.max_lat)

        if 1: #https://github.com/OpenDrift/opendrift/issues/362
            o.set_config('drift:stokes_drift', False)
            o.set_config('seed:wind_drift_factor', 0.035) 
        else: #Wind by itself is about 3% to 3.5%, but it already includes the StokesDrift (which accounts for 1.5% of these 3.5%). So if we want to add StokesDrif, the wind fraction is reduced to 2%
            o.set_config('drift:stokes_drift', True)
            o.set_config('seed:wind_drift_factor', 0.02) 

        # Usa o Runge-Kutta como metodo numerico (ou Euler by default)
        if rk4:
            o.set_config('drift:advection_scheme', 'runge-kutta4')


        if verbose:
            print('Seeding elements.\n')
        o.seed_elements(lat    = self.sim_cfg_file.spill_lat,
                        lon    = self.sim_cfg_file.spill_lon,
                        number = self.sim_cfg_file.num_seed_elements,
                        radius = self.sim_cfg_file.spill_radius,
                        time   = datetime.strptime(self.sim_cfg_file.start_date, "%Y-%m-%d"),#.replace(hour=1, minute=45, second=0),
                        oil_type = "SOCKEYE SWEET",
                        )
        


        ############## RUN SIMULATION ############## 
        if verbose:
            print('Simulation started.\n')


        result_file = RunASimulation.generate_result_fname(self.sim_cfg_file.simulation_id, 0)
        raw_results_folder = os.path.join(self.result_path, "raw/") 
        os.makedirs(raw_results_folder, exist_ok=True)
        result_rel_path = os.path.join(raw_results_folder, result_file)  # Path do arquivo onde salvar o resultado da simulação

        o.run(time_step = self.sim_cfg_file.time_step, # Time step para a simulação
            time_step_output = self.sim_cfg_file.output_time_step, # Time step para ocupar menos espaço de memória
            end_time = datetime.strptime(self.sim_cfg_file.end_date, "%Y-%m-%d"),
            outfile = result_rel_path,
            stop_on_error = True,
            )
 
        result_gif_file = RunASimulation.generate_result_fname(self.sim_cfg_file.simulation_id, 1)
        gif_results_folder = os.path.join(self.result_path, "gif/") 
        os.makedirs(gif_results_folder, exist_ok=True)
        gif_rel_path = os.path.join(gif_results_folder, result_gif_file)
        if ((self.gif_config.min_lon < self.sim_cfg_file.min_lon) or (self.gif_config.min_lat < self.sim_cfg_file.min_lat) or (self.gif_config.max_lon > self.sim_cfg_file.max_lon) or (self.gif_config.max_lat > self.sim_cfg_file.max_lat)):
            print("Cuidado: o gif tem um quadramento maior do que foi simulado, e as particulas foram desativadas fora do domínio.")
        o.animation(filename=str(gif_rel_path), corners = [self.gif_config.min_lon, self.gif_config.max_lon, self.gif_config.min_lat, self.gif_config.max_lat], background=['x_sea_water_velocity', 'y_sea_water_velocity'], vmin=-1, vmax=1, fast=True, fps=6)


        print(f"... simulação {self.sim_cfg_file.simulation_id+1} terminada com sucesso")
        return 