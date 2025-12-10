#@brief Download metaoceanographic data from the Copernicus website
#@file tecdrift/downloader.py
#@author Bruno Kassar, Instituto Tecgraf/PUC-Rio
#@date August 13th 2025
#Download the Environmental fields of winds, currents and waves
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from opendrift.models.oceandrift import OceanDrift
#from opendrift.models.leeway import Leeway
from opendrift.models.openoil import OpenOil

from downloader import TecDriftDownloader
# Leitor de dados NetCDF/OPeNDAP
from opendrift.readers import reader_netCDF_CF_generic

#Diretório onde estão os arquivos netCDF de dados metaoceanográficos
metocean_dir = "D:/DATA/oildrift/dados_copernicus"
fname_case = "D:/DATA/oildrift/casos/caso_1.json"
verbose = True


outfile = str(Path(fname_case).with_suffix(".nc"))#arquivo para salvar o resultado da simulacao
case_dict = None
with open(fname_case, 'r') as file:
  case_dict = json.load(file)
  if case_dict == None:
    print('Erro na leitura do arquivo de configuração do caso!')
    quit()

D = TecDriftDownloader(case_dict = case_dict,output_directory=metocean_dir)
current_fname = D.GetCurrentFileName()
wind_fname    = D.GetWindFileName()
#wave_fname    = D.GetWaveFileName()
#a correnteza para este dominio espaço-temporal não existe no diretório
if not os.path.isfile(current_fname):  
  D.DownloadCurrent()

#o vento para este dominio espaço-temporal não existe no diretório
if not os.path.isfile(wind_fname):
  D.DownloadWind()

#if not os.path.isfile(wave_fname):
#  D.DownloadWave()

#Criação do OpenOil
#o = OpenOil(loglevel=50)
o = OceanDrift(loglevel=20 if verbose else 50)

reader_current = reader_netCDF_CF_generic.Reader(current_fname)
reader_wind    = reader_netCDF_CF_generic.Reader(wind_fname   )
o.add_reader([reader_current, reader_wind])
if verbose:
  print('Current Reader details:\n')
  print(reader_current)
  print('Wind Reader details:\n')
  print(reader_wind)

#o.set_config('environment:constant:x_wind', 0)
#o.set_config('environment:constant:y_wind', 0)
#o.set_config('environment:constant:x_sea_water_velocity', 0)
#o.set_config('environment:constant:y_sea_water_velocity', 0)
#o.set_config('environment:constant:sea_surface_wave_significant_height', 0)

# Desativa particulas fora do dominio
o.set_config('drift:deactivate_west_of' , case_dict["min_lon"])
o.set_config('drift:deactivate_east_of' , case_dict["max_lon"])
o.set_config('drift:deactivate_south_of', case_dict["min_lat"])
o.set_config('drift:deactivate_north_of', case_dict["max_lat"])

if 1: #https://github.com/OpenDrift/opendrift/issues/362
  o.set_config('drift:stokes_drift', False)
  o.set_config('seed:wind_drift_factor', 0.035) 
else: #Wind by itself is about 3% to 3.5%, but it already includes the StokesDrift (which accounts for 1.5% of these 3.5%). So if we want to add StokesDrif, the wind fraction is reduced to 2%
  o.set_config('drift:stokes_drift', True)
  o.set_config('seed:wind_drift_factor', 0.02) 

#o.set_config('processes:evaporation', True)
#o.set_config('processes:emulsification', True)

# Usa o Runge-Kutta como metodo numerico (+ preciso que o Euler default)
o.set_config('drift:advection_scheme', 'runge-kutta4')

if verbose:
  print('Seeding elements.\n')
o.seed_elements(
    lat   = case_dict['spill_lat'],
    lon   = case_dict['spill_lon'],    
    number= case_dict['num_elements'],
    radius= case_dict['spill_radius'],
    time=datetime(*case_dict['start_datetime']))


if verbose:
  print('Simulation started.\n')
o.run(time_step=case_dict['time_step'],
      end_time=datetime(*case_dict['end_datetime']),
      outfile=outfile,
      stop_on_error = True
      )

#o.plot(
#    corners=[case_dict["min_lon"],
#             case_dict["max_lon"],
#             case_dict["min_lat"],
#             case_dict["max_lat"]])

if verbose:
  print('Plotting results.\n')
o.plot(corners=[case_dict["min_lon"],
                case_dict["max_lon"],
                case_dict["min_lat"],
                case_dict["max_lat"]],
       background=['x_sea_water_velocity', 'y_sea_water_velocity'], # Mostra as correntes no fundo
       skip=3, # Pula alguns vetores de fundo para não poluir
       filename=fname_case + '.png' # Salva o arquivo
    )


if 0:
  o.animation(
        corners=[case_dict["min_lon"],
        case_dict["max_lon"],
        case_dict["min_lat"],
        case_dict["max_lat"]],
        background=['x_sea_water_velocity', 'y_sea_water_velocity'], # Mostra as correntes no fundo
        skip=3, # Pula alguns vetores de fundo para não poluir
        filename=fname_case + '.gif' # Salva o arquivo
        )