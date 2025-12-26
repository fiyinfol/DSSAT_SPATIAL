import xarray as xr
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import re
import os
import subprocess
from datetime import datetime
import pandas as pd
import cftime
from netCDF4 import Dataset, num2date
import sys

#cultivar= sys.argv[1]
input_weatherfileNC= sys.argv[1]
dssat_output_file_netcdf=sys.argv[2]


dssat_weather_file = 'TEST5155.WTH'
weather_code = "TEST5155"
expInFilename = "TEMA8001.MZX"
expOutFilename = "writing.mzx"
#input_weatherfileNC = 'cregridclimate2.nc'
dssat_output_file = "Summary.OUT"
#dssat_output_file_netcdf ="obat_2msimu_50_nofer.nc"
input_soilfileNC = 'AFRICA_Soil.nc'
soil_code1 = "HC_GEN00"
soil_code2 = "HC_GEN000"

no_of_years = "120"
start_year = "80"   #please use this format of two number to indicate start year
jan_simulaton_date = "01-01-1980"
December_maximum_planting = "31-12-1980" # please ensure dd-mm-yyyy

cultivar= "GH0004 OBATAMPA"
fertilizerInc="africa_fertilizer_mai_regrided_1850_2015.nc"
plantingDatenc = "Africa_regirded_mai_rf_ggcmi_crop_calendar_phase3_v1.01.nc4"
fertilizer_brand = "i" # if you want issimip write i, if you want a constant level write c
fertilizer_level = "40"
fertil_switch = "1"  #please note that 0 is for no fertilizer and 1 for include fertilizer

variable_names = ['rsds','tmax', 'tmin', 'pr']			#geoengineering



with xr.open_dataset(input_weatherfileNC) as ds_wdata:     #opens weather netcdf
    longitude = ds_wdata['lon'].values
    latitude = ds_wdata['lat'].values
    times = ds_wdata['time'].values 
    


   
    grainName = 'cyield'
    vegeName = 'topw'
    pldaName = 'pldat'
    soilName = 'swxmext'
    ETSimName = 'etcmsim'
    ETplantName = 'etcplan'
    #creating a summary.OUT netcdf file
    ds_output = CreateNetcdf(dssat_output_file_netcdf, grainName, vegeName, pldaName, soilName, ETSimName, ETplantName, longitude, latitude)
    init_time = 1
    with xr.open_dataset(input_soilfileNC) as ds_sdata:
        with xr.open_dataset(fertilizerInc) as fert_data:
            with xr.open_dataset(plantingDatenc) as plant_data:
       
        
                for i in range(1,len(longitude)):
                    for j in range(1,len(latitude)):
                    #print(latitude[j])
               
                
                        soilvalueCode= ReadSoilNC(ds_sdata, i, j)
                
                
                
    
                
                        if str(soilvalueCode) == "nan":              # maskData <= 0 or
                        # print(f" {counter} skipped. location not on land.")
                            continue


                
                        #Reads in weather data from netcdf
                        weatherData = ReadWeatherNC(ds_wdata, variable_names, i, j)
                        #RHum = ds_wdata['hurs'].values[:,j,i]
                        WriteWeatherASCII(dssat_weather_file,times, weatherData)
                        if fertilizer_brand == "i" :
                            fertilcoden = ReadfertilizerNC(fert_data, i, j)
                            if fertilcoden < 15:
                                fertilcode = 15
                            elif fertilcoden >= 15:
                                fertilcode = fertilcoden        
                        elif fertilizer_brand == "c" :
                            fertilcode = fertilizer_level


                        if soilvalueCode < 10:
                            soilData =soil_code2  + str(int(soilvalueCode))

                        if soilvalueCode >= 10:
                            soilData =soil_code1  + str(int(soilvalueCode))
               
                        planting_code = ReadplantingNC(plant_data, i, j)
			
                        if planting_code < 10:
                       	    planting_date = start_year +  str(0) + str(0) + str(int(planting_code))
                       	    simu_date = jan_sim_date
                       	elif planting_code <= 60:
                            planting_date = start_year +  str(0) + str(int(planting_code))
                            simu_date = jan_sim_date
		
                        elif planting_code > 60 and planting_code < 100:
                            planting_date = start_year + str(0) + str(int(planting_code))
                            cal_sim_date = planting_code - 60
                            if cal_sim_date >= 10 and  cal_sim_date <= 40:
                                simu_date = start_year + str(0) +  str(int(cal_sim_date))
                            elif cal_sim_date <= 9:
                                simu_date = jan_sim_date
                        elif planting_code >= 100 and planting_code <= 334:
                            planting_date = start_year  + str(int(planting_code))
                            cal_sim_date = planting_code - 60
                            if cal_sim_date >= 100:
                                simu_date = start_year + str(int(cal_sim_date))
                            elif cal_sim_date >= 10 and  cal_sim_date < 100:
                                simu_date = start_year + str(0) +  str(int(cal_sim_date))
                            cal_min_date = planting_code - 30

                        elif planting_code >= 335 :
                            planting_date = start_year  + str(int(planting_code))
                            simu_date = start_year  + str(int(planting_code - 60))
       

                                    

                        print(latitude[j])
                        print(longitude[i])
                        print(cultivar)
                        print(simu_date)
                        print(fertilcode)
                        
    
                     
                

  
                        ModifyExpFile(expInFilename, expOutFilename, weather_code, soilData,simu_date,min_planting,cultivar,no_of_years,fertilcode,maximum_planting,planting_date,planting_date_function,fertil_switch)
                        # running dssat
                        dssat = "./dscsm048 MZIXM048 C writing.mzx 1"
                        #dssat = "./dscsm048 MZCER048 C writing.mzx 1"
                
                        subprocess.call(dssat, shell=True)
                
                        if not os.path.exists(dssat_output_file):
                            print(f"Error:DSSAT output file not found")
                            continue
                        yields, sdates, vegeyield,plantdate, soilmoex, etansim, etplan = ReadSummaryOUT(dssat_output_file)
            
                        itime = 1
                        WriteDataToNetcdf(ds_output, init_time, grainName, vegeName, pldaName, soilName, ETSimName, ETplantName, sdates, yields, vegeyield, plantdate,  soilmoex, etansim, etplan, longitude[i], latitude[j])
                        init_time = 0
             
    ds_output.close()
                
                
    
                
print("it is done")    

