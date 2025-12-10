#@brief Download metaoceanographic data from the Copernicus website
#@author Louis Pottier, Instituto Tecgraf/PUC-Rio
#@date December 2025

import os
from datetime import datetime
import copernicusmarine
from omegaconf import DictConfig
from exceptions.CustomExceptions import DownloadCurrentError, DownloadWindError

class Fetch:
    """
    Downloads environment (wind and current) data from the Copernicus Marine Data Store
  
    Attributes:
          cm_data (DictConfig): The Copernicus Marine configuration object
          start_date_datetype (datetime): The initial date for data fetching
          end_date_datetype (datetime): The final date for data fetching
          user (str): The login username
          pwd (str): The login password
    """
    def __init__ (self, cm_config_file : DictConfig, login_config_file : DictConfig):
      """
      Initializes the Fetch class
    
      Attributes:
            cm_config_file (DictConfig): The Copernicus Marine configuration object
            login_config_file (DictConfig): The login configuration object
        """
      self.cm_data = cm_config_file
      self.start_date_datetype = datetime.strptime(cm_config_file.start_date, "%Y-%m-%d")
      self.end_date_datetype = datetime.strptime(cm_config_file.end_date, "%Y-%m-%d")
      self.user = login_config_file.user
      self.pwd  = login_config_file.password


    def set_credentials(self, user: str, pwd: str):
      self.user = user
      self.pwd  = pwd


    #Para baixar a correnteza
    def DownloadCurrent (self):
      print(f"Busca de dados de correnteza...\n")
      try:
        copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m", #ID do banco de dados no site Copernicus Marine Data Store, 
        variables=["uo", "vo"],                              # Sub-conjunto de variáveis presentes nos dados relativos ao ID escolhido
        username          = self.user,
        password          = self.pwd,
        minimum_longitude = self.cm_data.min_lon,
        maximum_longitude = self.cm_data.max_lon,
        minimum_latitude  = self.cm_data.min_lat,
        maximum_latitude  = self.cm_data.max_lat,
        start_datetime    = self.cm_data.start_date,
        end_datetime      = self.cm_data.end_date,
        output_filename   = self.GetCurrentFileName(False),
        output_directory  = self.cm_data.field_directory
        )
      except Exception as e:
        raise DownloadCurrentError("Failed to download current data") from e
 
    #Para baixar vento
    def DownloadWind (self):
      print(f"Busca de dados de vento...\n")
      try:
        copernicusmarine.subset(
              dataset_id        = "cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H",
              variables         = ["eastward_wind", "northward_wind"], # Sub-conjunto de variáveis presentes nos dados relativos ao ID escolhido
              username          = self.user,
              password          = self.pwd,
              minimum_longitude = self.cm_data.min_lon,
              maximum_longitude = self.cm_data.max_lon,
              minimum_latitude  = self.cm_data.min_lat,
              maximum_latitude  = self.cm_data.max_lat,
              start_datetime    = self.cm_data.start_date,
              end_datetime      = self.cm_data.end_date,
              minimum_depth     = 0,
              maximum_depth     = 10,
              output_filename   = self.GetWindFileName(False),
              output_directory  = self.cm_data.field_directory
        )
      except Exception as e:
        raise DownloadWindError("Failed to download wind data") from e

    def GetDatetimeStr (self,dt):
      return f"({dt.year}-{dt.month}-{dt.day}-{dt.hour}-{dt.minute}-{dt.second})"
    
    def GetDomainStr (self):
      return f"({int(self.cm_data.min_lon)},{int(self.cm_data.max_lon)},{int(self.cm_data.min_lat)},{int(self.cm_data.max_lat)})"

    def GetSpatiotemporalStr (self):
      return f"{self.GetDatetimeStr(self.start_date_datetype)}{self.GetDatetimeStr(self.end_date_datetype)}{self.GetDomainStr()}"

    def GetCurrentFileName (self, with_folder = True):
      fname = f"current_{self.GetSpatiotemporalStr()}.nc" 
      if with_folder:
        fname = os.path.join(self.cm_data.field_directory, fname)
      return fname

    def GetWindFileName (self, with_folder = True):
      fname = f"wind_{self.GetSpatiotemporalStr()}.nc"
      if with_folder:
        fname = os.path.join(self.cm_data.field_directory, fname)
      return fname


    def download_data(self):
      current_fname = self.GetCurrentFileName(with_folder = True)
      wind_fname    = self.GetWindFileName(with_folder = True)

      #Caso a correnteza para este dominio espaço-temporal não exista no diretório, vai buscar no site Copernicus os dados associados e salvá-los
      if not os.path.exists(current_fname):
          print(f"     Dados de correnteza não encontrados no diretório {self.cm_data.field_directory}. Downloading...")
          self.DownloadCurrent()
      else:
          print(f"     Dados de correnteza já presentes no diretório {self.cm_data.field_directory}")


      #Caso o vento para este dominio espaço-temporal não exista no diretório
      if not os.path.exists(wind_fname):
          print(f"     Dados de vento não encontrados no diretório {self.cm_data.field_directory}.  Downloading...\n")
          self.DownloadWind()
      else:
          print(f"     Dados de vento já presentes no diretório {self.cm_data.field_directory}\n")