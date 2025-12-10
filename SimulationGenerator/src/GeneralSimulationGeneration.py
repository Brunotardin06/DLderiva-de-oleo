#@brief Parent class to prepare the generation of many simulations
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

from hydra import initialize, compose
from omegaconf import OmegaConf
import os
from src.RunASimulation import RunASimulation
from src.Fetch import Fetch
from tqdm import tqdm
from multiprocessing import Pool
from abc import abstractmethod
from exceptions.CustomExceptions import MainConfigFileNotFound, CredentialsConfigFileNotFound, GifConfigFileNotFound, ReferenceSimulationConfigFileNotFound, TimestepOverOutputTimestep

class GeneralSimulationGeneration:
    """
    Generates various simulations based on user-defined parameters.

    Attributes:
        config_folder (str): The name of the folder containing all YAML configuration files.
        configlist_file (str): The name of the YAML configuration file (including  .yaml extension)
            that lists the parameters for each simulation.
        principal_cfg (DictConfig): The main configuration object, which provides paths and
            general simulation information.
        gif_cfg (DictConfig): The configuration object for animation output of Opendrift runs.
        param_cfg (DictConfig): The reference configuration used as a template when generating
            the configuration list.
        login_cfg (DictConfig): The login configuration object.
        cm_cfg (DictConfig): The Copernicus Marine configuration object.
    """
    def __init__ (self, config_folder: str, reference_config_file: str, configlist_file: str):
        """
        Initializes the simulation generator by loading the required YAML configurations.

        Args:
            config_folder (str): The folder containing all YAML configuration files.
            reference_config_file (str): The name of the YAML configuration file (without
                extension) that identifies the reference configuration used to build
                `param_cfg`.
            configlist_file (str): The YAML filename (including .yaml extension) that lists the
                simulation parameters to be generated.
            
        """
        self.config_folder = f"../{config_folder}"
        self.configlist_file = configlist_file

        verifpath = os.path.join(config_folder, "main" + ".yaml")
        print(verifpath)
        if not os.path.exists(verifpath):
            raise MainConfigFileNotFound(f"Main configuration file not found in {config_folder}")
        
        with initialize(config_path=self.config_folder, version_base=None):
            self.principal_cfg = compose(config_name="main")

            verifpath = os.path.join(config_folder, self.principal_cfg.configs.gif_config + ".yaml")
            print(verifpath)
            if not os.path.exists(verifpath):
                raise GifConfigFileNotFound(f"GIF configuration file not found in {config_folder}")
            self.gif_cfg = compose(config_name=self.principal_cfg.configs.gif_config)

            self.principal_cfg.configs.base_sim_config = f"{reference_config_file}"
            verifpath = os.path.join(config_folder, self.principal_cfg.configs.base_sim_config +".yaml")
            if not os.path.exists(verifpath):
                raise ReferenceSimulationConfigFileNotFound(f"Reference configuration file not found in {config_folder}. This file should be generated in the GUI classes execute_button method.")
            self.param_cfg = compose(config_name=self.principal_cfg.configs.base_sim_config)

            verifpath = os.path.join(config_folder, self.principal_cfg.configs.cm_login +".yaml")
            if not os.path.exists(verifpath):
                raise CredentialsConfigFileNotFound(f"Login information configuration file not found in {config_folder}")
            self.login_cfg = compose(config_name=self.principal_cfg.configs.cm_login)

            verifpath = os.path.join(config_folder, self.principal_cfg.configs.cm_config +".yaml")
            if not os.path.exists(verifpath):
                raise CredentialsConfigFileNotFound(f"Copernicus Marine data information configuration file not found in {config_folder}")
            self.cm_cfg = compose(config_name=self.principal_cfg.configs.cm_config)

    

    def set_result_folder(self, result_folder: str):
        """
        Redefines the folder where Opendrift simulation results will be stored.

        Args:
            result_folder (str): Name of the subfolder to create inside the main
                results directory.
        """
        base_path = self.principal_cfg.paths.sim_results_location
        self.principal_cfg.paths.sim_results_location = os.path.join(base_path, result_folder)

    
    def timestep_correction(self) -> int :
        """
        """
        original_timestep = self.param_cfg.time_step
        ratio = self.param_cfg.output_time_step/original_timestep
        new_timestep = original_timestep
        while (((ratio*10) % 10 != 0) and (new_timestep <= self.param_cfg.output_time_step)): #if ratio not integer
                new_timestep += 1
                ratio = self.param_cfg.output_time_step/new_timestep
        if new_timestep > self.param_cfg.output_time_step:
            raise TimestepOverOutputTimestep(f"Timestep reach the Output timestep value.")
        else:
            if new_timestep != original_timestep:
                print(f"Time step updated from {original_timestep} to {new_timestep} for Opendrift ratio consistency (ratio = {ratio})")
        return new_timestep


    @abstractmethod
    def generate_sim_configs(self, *args):
        """
        Generates all simulation configurations and stores them in a single YAML file.

        Subclasses must implement this method. The method signature is flexible to allow
        subclasses to use different argument lists.

        Args:
            *args: Positional arguments required by the specific subclass implementation.
        """
        pass



    @staticmethod
    def warp_simulate(args):
        """
        Executes a single simulation (typically used inside a multiprocessing worker).

        Args:
            args (tuple): A tuple containing:
                - Simulator: an instance of the simulator class
                - cfg: the configuration file or object to use
                - verbose (bool): whether to enable verbose output
                - rk4 (bool): whether to use the RK4 integration scheme
        """
        Simulator, cfg, verbose, rk4 = args
        Simulator.set_sim_config_file(cfg)
        Simulator.run_simulation(verbose, rk4)
        

    def generate_simulations(self, number_of_workers: int, verbose: bool, rk4flag: bool, overwrite: bool):
        """
        Executes all simulations using multiprocessing.

        Args:
            number_of_workers (int): Number of worker processes to use.
            verbose (bool): Whether to enable verbose output for each simulation.
            rk4flag (bool): Whether to use the RK4 integration scheme.
        """
        results_relpath = self.principal_cfg.paths.sim_results_location
        if os.path.exists(results_relpath):
            if overwrite:
                print(f"Overwriting existing results folder {results_relpath}.")
            else:
                raise FileExistsError(f"Results folder '{results_relpath}' already exists. Select the overwrite option or rename the result folder.")


        print("\n")
        print(f"1/3 Fetching Copernicus Data...")
        F = Fetch(self.cm_cfg, self.login_cfg)
        F.download_data()
        
    
        print("\n")
        print(f"2/3 Retrieving configuration file list...")
        Simulator = RunASimulation(self.config_folder, self.principal_cfg)
        sims_conf_folder = self.principal_cfg.paths.list_sim_configs_location
        relpath = os.path.join(sims_conf_folder, self.configlist_file)
        if os.path.exists(relpath):
            list_all_sims = OmegaConf.load(relpath)
        else:
            raise FileNotFoundError("GeneralSimulationGeneration: YAML Configuration file doesn't exist: either not found or not created.")
        
        list_to_simulate = []
        list_to_simulate = list_all_sims # We execute all simulations
        print(f"3/3 Running simulations from all configuration files with {number_of_workers} processors...")
        print("\n")
        params = [(Simulator, cfg, verbose, rk4flag) for cfg in list_to_simulate]
        with Pool(processes=number_of_workers) as pool:
            _ = list(tqdm(pool.imap(self.warp_simulate, params), total=len(params)))
        print(f"Resultados gerados com sucesso na pasta '{self.principal_cfg.paths.sim_results_location}'.")