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


dssat_weather_file = 'TEST5155.WTH'
weather_code = "TEST5155"
expInFilename = "TEMA8001.MZX"
expOutFilename = "writing.mzx"
input_weatherfileNC = 'cregridclimate2.nc'
dssat_output_file = "Summary.OUT"
dssat_output_file_netcdf ="afri_yield.nc"
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

#extracting sim date to a format dssat can use
jan_sim_date= datetime.strptime(jan_simulaton_date, '%d-%m-%Y').strftime('%y%j')

dec_max_date= datetime.strptime(December_maximum_planting, '%d-%m-%Y').strftime('%y%j')

def WriteWeatherASCII(dssat_weather_file, times, wDataArray):

        with open(dssat_weather_file, 'w') as output_file:
                # Write weather data header
                output_file.write("*WEATHER DATA : TEST\n")
                output_file.write("\n")
                output_file.write("@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n")
                output_file.write("       -28.067   30.133   300  17.7   7.7 -99.0 -99.0\n")
                output_file.write("@DATE  SRAD  TMAX  TMIN  RAIN  WIND RHUM\n")

                #dividing in row and colomns
                wDataArray = list(map(list, zip(*wDataArray)))

                # Write data with rounding and date formatting
                for time_idx, values in enumerate(wDataArray):
                
                        time_obj= times[time_idx]
                        
                        if isinstance(time_obj,np.datetime64):
                             time_obj = pd. to_datetime(time_obj).to_pydatetime()
                        year = time_obj.year
                        day_of_year = time_obj.timetuple().tm_yday
                            
                            
                        
                        #format year and DOY as YYDDD
                            
                        
                        year_day_of_year = f'{year % 100:02d}{day_of_year:03d}'
                        #year_day_of_year = datetime.utcfromtimestamp(times[time_idx].astype(int) * 1e-9).strftime('%y%j')

                        # Round values to one decimal point
                        rounded_values = [str(round(value, 1)) for value in values]
                        rounded_values = [value.rjust(5) for value in rounded_values]

                        # Use double spaces as delimiter
                        output_file.write("{} {}\n".format(year_day_of_year, ' '.join(rounded_values)))

# expfilename = "writing.mzx"
def ModifyExpFile(expinputfilename, expoutfilename,weather_code,soilData,simulate_date,mina_plant,culti,nyears,fcode,maxa_planting,plata_date,plfunction,fertil_on): #ModifyExpFile(expInFilename, expOutFilename, weather_code, soilData,simu_date,min_planting,cultivar)
        with open(expinputfilename, "r") as fdata:
                content = fdata.readlines() 
                with open(expoutfilename, "w+") as fdata2:
                        #changing the weather and soil
                        conpute_line = content[12]
                        zero_count = 0
                        new_line = ""
                        for char in conpute_line:
                            if char == "0":
                                zero_count += 1
                                if zero_count == 4:
                                    new_line += str(fertil_on)  # Replace 3rd zero
                                    continue
                            new_line += char

    # Replace the original line
                        new_conpute_line = content[12] = new_line


                        content_line = content[20]
                        new_content_line = content_line.replace("KWAZ8031", weather_code).replace("UTUT000020",soilData)
                        #changing simulation date
                        fertilizer_line = content[76]
                        new_fertilizer_line= fertilizer_line.replace("415",str(fcode).rjust(3))
                        simulation_line =content[88]
                        new_simulation_line = simulation_line.replace("839", nyears.rjust(3)).replace("80001", simulate_date)

                        #changing minmal planting date
                        minimal_line = content[100]
                        new_minimal_line = minimal_line.replace("80030", mina_plant).replace("80366", maxa_planting)

                        #changing cultivar
                        cultivar_line = content[16]
                        new_cultivar_line = cultivar_line.replace("990005 SHORT TRIAL", culti)
                        #changing planting date
                        planting_line = content[43]
                        new_planting_line = planting_line.replace("80289", plata_date)

        

                        #planting date
                        #planting_date = "f" #input("is planting automatic or fixed, if fixed write f and if automatic write a: ")
                        if plfunction == "a":
                                        planting = content[94]
                                        automatic = planting.replace("R", "F", 1)  # A is just automatic planting while F is automatic planting that forces planting on the last day of the window
                                        fdata2.writelines(content[0:12])
                                        fdata2.writelines(new_conpute_line)
                                        fdata2.writelines(content[13:16])
                                        fdata2.writelines(new_cultivar_line)
                                        fdata2.writelines(content[17:20])
                                        fdata2.writelines(new_content_line)
                                        fdata2.writelines(content[21:76])
                                        fdata2.writelines(new_fertilizer_line)
                                        fdata2.writelines(content[77:88])
                                        fdata2.writelines(new_simulation_line)
                                        fdata2.writelines(content[89:94])
                                        fdata2.writelines(automatic)
                                        fdata2.writelines(content[95:100])
                                        fdata2.writelines(new_minimal_line)
                                        fdata2.writelines(content[101:112])

                                      
        
                        elif plfunction == "f":
                                        fdata2.writelines(content[0:12])
                                        fdata2.writelines(new_conpute_line)
                                        fdata2.writelines(content[13:16])
                                        fdata2.writelines(new_cultivar_line)
                                        fdata2.writelines(content[17:20])
                                        fdata2.writelines(new_content_line)
                                        fdata2.writelines(content[21:43])
                                        fdata2.writelines(new_planting_line)
                                        fdata2.writelines(content[44:76])
                                        fdata2.writelines(new_fertilizer_line)
                                        fdata2.writelines(content[77:88])
                                        fdata2.writelines(new_simulation_line)
                                        fdata2.writelines(content[89:100])
                                        fdata2.writelines(new_minimal_line)
                                        fdata2.writelines(content[101:112])
                                    


def ReadSummaryOUT(dssat_output_file):
    dlent = 0

    # Determine the number of lines in the file
    with open(dssat_output_file, "r") as fdata: 
        dlent = len(fdata.readlines())

    dssatSum = np.empty(shape=(dlent-3, 85))  # Prepare an empty array for data
    headers = []

    skip = 0
    isHeader = True
    count = 0

    # Function to safely convert values to float
    def safe_float_conversion(value):
        try:
            return float(value)
        except ValueError:
            # Return NaN for any invalid value
            return float('nan')

    with open(dssat_output_file, "r") as fdata:
        for line in fdata.readlines():
            if skip < 3:
                skip = skip + 1
                continue

            parts = line.split()
            
            if len(parts) < 98:
                print(f"Skipping line {count+1} due to insufficient columns: {parts}")
                continue  # Skip this line if it doesn't have enough columns

            for i in range(13, 98):
                 parts[i] = parts[i].replace("*", "9")

            # Process headers only once
            if isHeader:
                headers = parts[14:98]
                isHeader = False
            else:
                values = [safe_float_conversion(value) for value in parts[13:98]]

                # Ensure we have exactly 85 values
                while len(values) < 85:
                    values.append(float('nan'))  # Fill missing values with NaN
                if len(values) > 85:
                    values = values[:85]  # Trim extra values if necessary

                dssatSum[count] = values
                count += 1
    colname = 'hwam'
    colnum = -1
    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == colname.lower():
            colnum = i

    variable1 = dssatSum[:,colnum] #yield 


    vegetative = 'CWAM'
    vegnum = -1
    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == vegetative.lower():
            vegnum = i
    vegtop= dssatSum[:,vegnum]


    SMextratable = 'SWXM'
    soilnum = -1
    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == SMextratable.lower():
            soilnum = i
    SMextract= dssatSum[:,soilnum]


    

    Evaposimulate = 'ETCM'
    etsimnum = -1
    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == Evaposimulate.lower():
            etsimnum = i
    evaposim= dssatSum[:,etsimnum]

    Evapoplant = 'ETCP'
    etplanum = -1
    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == Evapoplant.lower():
            etplanum = i
    evapopla= dssatSum[:,etplanum]



    day_of_year = "SDAT"    #simulation date used as time in the netcdf, it was used bescause regarless if there was crop failure each year will still have simulation date
    dnum = -1

    for i in range(1,len(headers)):
        head = headers[i]
        if head.lower() == day_of_year.lower():
            dnum = i


    dateColumn = dssatSum[:,dnum]
    datelenght = len(dateColumn)
    
    res = []     #simulation date

    for i in range(datelenght):
        if not pd.isna(dateColumn[i]):
            data = int(dateColumn[i])
            if data > 0:
                try:
                    res.append(datetime.strptime(str(data), "%Y%j").strftime("%Y"))
                except ValueError as e:
                    print(f"Error processing data '{data}': {e}")

    
    res = np.array([np.datetime64(date) for date in res])


    colyear = 'pdat'
    ynum = -1

    for i in range(1, len(headers)):
        if headers[i].lower() == colyear.lower():
            ynum = i

    plantcolumn = dssatSum[:, ynum]
    plantlength = len(plantcolumn)

    plantres = []

    for i in range(plantlength):
        val = plantcolumn[i]

        if not np.isnan(val):
            try:
                # Ensure clean int, remove any float issues like 1980183.0
                pdata = str(int(val)).strip()
                if len(pdata) == 7:
                    doy = int(pdata[4:])  # Get last 3 digits only
                    plantres.append(doy)
                    #print(f"Extracted DOY from {pdata}: {doy}")
                else:
                    print(f"Skipping invalid pdata: {pdata}")
            except Exception as e:
                print(f"Error parsing value {val}: {e}")
                continue
             
    
  
    return variable1, res, vegtop, plantres, SMextract, evaposim, evapopla 
    
    
    





def CreateNetcdf(dssat_output_file_netcdf, gName, vName, pName, sName, ETsimuName, ETplName, lons, lats):
    nlon = len(lons)
    nlat = len(lats)
    missingval = 3e-16

   # Check if the file exists
    if not os.path.isfile(dssat_output_file_netcdf):
        # If it doesn't exist, create the file
        with nc.Dataset(dssat_output_file_netcdf, 'w', format='NETCDF4') as ds:
            # Define dimensions
            ds.createDimension('lon', nlon)
            ds.createDimension('lat', nlat)
            ds.createDimension('time', None)  # 'unlimited' time dimension
            ds.createDimension('string_len', 10)  # Maximum length of the date string 'dd-mm-yyyy' is 10

            # Create variables
            lon_var = ds.createVariable('lon', 'f4', ('lon',))
            lat_var = ds.createVariable('lat', 'f4', ('lat',))
            time_var = ds.createVariable('time', 'f8', ('time',))
            yield_var = ds.createVariable(gName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval)
            veg_var = ds.createVariable(vName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval)
            soil_var = ds.createVariable(sName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval)
            ET_sim_var = ds.createVariable(ETsimuName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval)
            ET_plan_var = ds.createVariable(ETplName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval)
            planting_var = ds.createVariable(pName, 'f4', ('time', 'lat', 'lon',), fill_value=missingval) # String type with length 10 # String type with length 10
            
    

            # Set variable attributes
            lon_var[:] = lons
            lat_var[:] = lats

            # Set global attributes
            ds.setncattr('attr', 'value')
            yield_var.setncattr('attr', 'value')
            veg_var.setncattr('attr', 'value')
            planting_var.setncattr('attr', 'value')
            soil_var.setncattr('attr', 'value')
            ET_sim_var.setncattr('attr', 'value')
            ET_plan_var.setncattr('attr', 'value')

    # Open the file in append mode
    ds = nc.Dataset(dssat_output_file_netcdf, 'a', format='NETCDF4')

    return ds 




def WriteDataToNetcdf(ds, init_time,  gName, vName, pName,sName, ETsimuName, ETplName, sdates, yields, vegeyield, plantdate, soilmoex, etansim, etplan, lon, lat):
    # Find the index corresponding to lon and lat
    lon_index = np.where(ds.variables['lon'][:] == lon)[0][0]
    lat_index = np.where(ds.variables['lat'][:] == lat)[0][0]

    # Find the current length of the 'time' dimension
    current_time_length = len(ds.variables['time'][:])

    # Convert numpy.datetime64 to Python datetime objects
    sdates_python = [date.astype('datetime64[D]').tolist() for date in sdates]

    # Extract the year from each date in sdates
    sdates_years = [date.year for date in sdates_python]

    

    # Append years to the 'time' variable
    if init_time == 1: 
        ds.variables['time'][current_time_length:current_time_length+len(sdates_years)] = sdates_years
   

        

    # Write yield values to the NetCDF file
    for year, yield_value, veg_value, pdate_value, sm_value, etsim_value, etplan_value in zip(sdates_years, yields, vegeyield, plantdate,soilmoex, etansim, etplan ):
        #Find the index corresponding to year
        
        whereyear = np.where(ds.variables['time'][:] == year)
        if whereyear[0].size == 0:
            print(f"Year {year} not found in 'time'. Skipping...")
            continue
        
        year_index = whereyear[0][0]
        #year_index = np.where(ds.variables['time'][:] == year)[0][0]
        
        # Write yield value to the NetCDF file
        ds.variables[gName][year_index, lat_index, lon_index] = yield_value
        ds.variables[vName][year_index, lat_index, lon_index] = veg_value
        ds.variables[sName][year_index, lat_index, lon_index] = sm_value
        ds.variables[ETsimuName][year_index, lat_index, lon_index] = etsim_value
        ds.variables[ETplName][year_index, lat_index, lon_index] = etplan_value
         # Convert the planting date to a list of characters
        #date_chars = np.array(list(pdate_value.ljust(10, ' ')), dtype='S1')
        
        
        # Write the planting date as a string to the NetCDF file
        #ds.variables[pName][year_index, lat_index, lon_index, :] = date_chars
        ds.variables[pName][year_index, lat_index, lon_index] =pdate_value
      


def ReadWeatherNC(ncdata, var_namelist, ilon, jlat):
    varArray = []
    for var in var_namelist:
        vdata = ncdata[var].values[:,jlat,ilon]

        #if var == 'dswrf':
                #vdata = vdata * conversion_factor  # there is conversion of solar radiation from watt/m2 to m2/d
        
        varArray.append(vdata)
    return varArray
    
def ReadSoilNC(ncdata, ilon, jlat):
    soil_value = ncdata['mask'].values[jlat,ilon]
    
    #combined_soil_code = soil_code  + str(soil_value)
    return soil_value


def ReadMaskNC(ncdata,ilon,jlat):
     mask_value = ncdata['Mask'].values[jlat,ilon]
     return mask_value


def ReadfertilizerNC(ncdata, ilon, jlat):
    fertilizer_value = (ncdata['fertrate'].mean(dim='time').values[jlat, ilon])
    if np.isnan(fertilizer_value):  # Check if it's NaN
        return 0  # Replace NaN with 0 (or any default value)
    
    return int(fertilizer_value)

def ReadplantingNC(ncdta, ilon, jlat):
     planting_value = ncdta['planting_day'].values[jlat,ilon]
     return planting_value


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

