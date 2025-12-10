# Simulation Data Generator

This project automatically generates wind and current data from the [Copernicus Marine Environment Monitoring Service (CMEMS)](https://data.marine.copernicus.eu/products?pk_vid=33ee4853ba1b53221759172724d8d500), creates YAML configuration files for simulations, and runs those simulations using the data for a specified range of dates.


## Features

- **User-friendly GUI** that allows users to customize folder names, configuration filenames, simulation parameters, run netCDF simulations and visualize results interactively.

- **Automatic environmental data download**: for every available option, the tool automatically fetches wind and current data from Copernicus Marine (CM) using the data configuration file specified in `main.yaml`.

- **Simulation Generator**: creates a set of simulation configuration files by combining user-defined parameters selected in the GUI.

- **Timestep Estimator**: generates simulation configurations, runs the simulations, analyzes convergence behavior, and helps the user choose an appropriate integration timestep. Visualization plots are produced automatically.

- **Optional multiprocessing** to run multiple simulations in parallel, reducing total runtime when supported by the system.


---



## How to Use

### 1. Create a folder (`conf/` by default)

This folder contains all the YAML configuration files necessary to execute the two available programs.

```
/conf
   main.yaml
   cm_data_config.yaml
   gif_frame_config.yaml
   cm_credentials_example.yaml
```

You can rename the `conf/` folder since its name will be asked on the opening GUI window.

### 1. Configure the Main YAML File (`main.yaml`)

This file indicates which configuration files to look for and which path to use for storing the configs and results. The name is fixed.

#### `main.yaml` by default

```yaml
configs:
  base_sim_config: null                          # YAML file name of the base simulation configuration file (empty by default)
  cm_config: "cm_data_config"                    # YAML file name of Copernicus Marine data configuration file
  gif_config: "gif_config"                       # YAML file name of the output GIF/animation configuration file
  cm_login: "cm_credentials"                     # YAML file name of the output GIF/animation configuration file

paths:
  list_sim_configs_location: "conf_lists/"  # Relative path to the directory where all generated sim configs are saved
  sim_results_location: "results/"          # Relative path to the output directory for simulation results
```

Make sure all paths are relative to the project root.



### 2. Configure the Copernicus Marine File (`cm_data_config.yaml` by default), the animation frame parameters File (`gif_frame_config.yaml` by default) and the login file (`cm_credentials_example.yaml` by default)

- The first file indicates the parameters used to fetch environment data (wind and current) from Copernicus Data.

- The second file are the latitudes and longitudes of the output animation, purely visualization

- The third file is the username and password in order to the program log in Copernicus Marine

The YAML file names are can be modified in the main


### 3. Launch the application `launcher.py`

You can now execute the main GUI script:
```bash
python launcher.py
```
The user should now insert the name of the folder containing all configuration files (`conf/` or another). Once done, the user can choose between the two options available.


## Output Structure

The folders and data are (by default) organized in the following structure:


```
/conf
   main.yaml
   cm_data_config.yaml**
   gif_frame_config.yaml**
   cm_credentials_example.yaml** 
```


```
/environment_data**
   wind_(2023-1-1-0-0-0)(2025-1-1-0-0-0)(2025-1-1-0-0-0)(-46,-37,-27,-21).nc
   current_(2023-1-1-0-0-0)(2025-1-1-0-0-0)(2025-1-1-0-0-0)(-46,-37,-27,-21).nc
   ...
```

```
/conf_lists
   default_simulations_configs.yaml* #By SimulationGenerator
   default_timesteps_sim_configs.yaml* #By TimestepEstimator
```

The output simulation files are organized by number in the following structure:

```
/results*
  /default_generation_folder*
    /raw
       result_0001.nc
       result_0002.nc
       ...
       result_0100.nc
    /gif
       result_0001.gif
       result_0002.gif
       ...
       result_0100.gif


  /default_timesteps_rk4*
    /raw
       result_0001.nc
       result_0002.nc
       ...
       result_0015.nc
    /gif
       result_0001.gif
       result_0002.gif
       ...
       result_0015.gif
```

*Renaming option is available on the GUI for these folders and files
**Renaming option is possible in the `conf/` YAML files