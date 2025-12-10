#@brief Download metaoceanographic data from the Copernicus website
#@file tecdrift/downloader.py
#@author Bruno Kassar, Instituto Tecgraf/PUC-Rio
#@date August 13th 2025
#Download the Environmental fields of winds, currents and waves

import os
import json
from datetime import datetime
import copernicusmarine


class TecDriftDownloader:
 def __init__ (self, case_dict=None, output_directory = None):
  if case_dict == None:
   self.min_lon=-46
   self.max_lon=-37
   self.min_lat=-27
   self.max_lat=-21
   self.start_datetime=datetime(2025,7,1,0,0,0)
   self.end_datetime  =datetime(2025,7,1,23,59,59)
  else:
   self.min_lon        = case_dict['min_lon'       ]
   self.max_lon        = case_dict['max_lon'       ]
   self.min_lat        = case_dict['min_lat'       ]
   self.max_lat        = case_dict['max_lat'       ]
   self.start_datetime= datetime(*case_dict['start_datetime'])
   self.end_datetime  = datetime(*case_dict['end_datetime'  ])
  #depois para voltar datetime para array de inteiros
  #[dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second]
  if output_directory == None:
   self.output_directory = "D:/DATA/oildrift/dados_copernicus"
  else:
   self.output_directory = output_directory

 #Objeto com as credenciais de Login no site do Copernicus.
 #É necessário criar um arquivo com os dados de login para cada usuário da seguinte forma:
 #Arquivo JSON salvo em C:/Users/username/copernicus_login_username.json do tipo
  #{
  #  "user": "login no site do copernicus",
  #  "pwd" : "senha"
  #}
 class CopernicusUserData:
  def __init__ (self):
   self.user = 'none'
   self.pwd  = 'none'
   user_dict = {'user':'noname', 'pwd':'none'} #dicionario vazio   
   user = os.getenv('username')
   loginfile = f'C:/Users/{user}/copernicus_login_{user}.json'
   with open(loginfile, 'r') as file:
    user_dict = json.load(file)
  
   if user_dict['user'] == None or user_dict['pwd']==None:
    print('Erro!\nArquivo com login do Copernicus não lido corretamente.')
    quit()   
   self.user = user_dict['user']
   self.pwd  = user_dict['pwd']

 #Para baixar a correnteza
 def DownloadCurrent (self):
  userdata = self.CopernicusUserData()
  copernicusmarine.subset(
   dataset_id="cmems_mod_glo_phy_anfc_merged-uv_PT1H-i",
   variables=["uo", "vo"],
   username=userdata.user,
   password=userdata.pwd,
   minimum_longitude=self.min_lon,
   maximum_longitude=self.max_lon,
   minimum_latitude =self.min_lat,
   maximum_latitude =self.max_lat,
   start_datetime   =self.start_datetime,
   end_datetime     =self.end_datetime,
   #minimum_depth=0,
   #maximum_depth=1.0,
   output_filename = self.GetCurrentFileName(False),
   output_directory = self.output_directory
  )
 
 
 #Para baixar vento
 def DownloadWind (self):
  userdata = self.CopernicusUserData()
  copernicusmarine.subset(
   dataset_id="cmems_obs-wind_glo_phy_nrt_l4_0.125deg_PT1H",
   variables=["eastward_wind", "northward_wind"],
   username=userdata.user,
   password=userdata.pwd,
   minimum_longitude=self.min_lon,
   maximum_longitude=self.max_lon,
   minimum_latitude =self.min_lat,
   maximum_latitude =self.max_lat,
   start_datetime   =self.start_datetime,
   end_datetime     =self.end_datetime,
   minimum_depth=0,
   maximum_depth=10,
   output_filename = self.GetWindFileName(),
   output_directory = self.output_directory
  )

 def GetDatetimeStr (self,dt):
  return f"({dt.year}-{dt.month}-{dt.day}-{dt.hour}-{dt.minute}-{dt.second})"
  
 def GetDomainStr (self):
  return f"({int(self.min_lon)},{int(self.max_lon)},{int(self.min_lat)},{int(self.max_lat)})"

 def GetSpatiotemporalStr (self):
  return f"{self.GetDatetimeStr(self.start_datetime)}{self.GetDatetimeStr(self.end_datetime)}{self.GetDomainStr()}"

 def GetCurrentFileName (self, add_dir = True):
  fname = f"current_{self.GetSpatiotemporalStr()}.nc"
  if add_dir:
   fname = os.path.join(self.output_directory,fname)
  return fname

 def GetWindFileName (self, add_dir = True):
  fname = f"wind_{self.GetSpatiotemporalStr()}.nc"
  if add_dir:
   fname = os.path.join(self.output_directory,fname)
  return fname
  

