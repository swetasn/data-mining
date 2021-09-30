import pandas as pd
from pandas import read_csv
import numpy as np

auto_mode = 'AUTO MODE ACTIVE PLGM OFF'
glucose_col = 'Sensor Glucose (mg/dL)'

def find_mean_percentage(data, dayCount):
    date_groups = data.groupby('Date')
    dates_percentage = (date_groups.count() / 288) * 100
    mean = np.sum(dates_percentage['time']) / dayCount

    if (len(data) == 0):
        return 0;
    else:
        return mean;

def find_percentage(data, dayCount):
    metrics_arr = []

    hyperglycemiaDf = data[data[glucose_col] > 180]
    metrics_arr.append(find_mean_percentage(hyperglycemiaDf, dayCount))

    hyperglycemiaCriticalDf = data[data[glucose_col] > 250]
    metrics_arr.append(find_mean_percentage(hyperglycemiaCriticalDf, dayCount))

    rangeDf = data[(data[glucose_col] >= 70) & (data[glucose_col] <= 180)]
    metrics_arr.append(find_mean_percentage(rangeDf, dayCount))
    
    rangeSecondaryDf = data[(data[glucose_col] >= 70) & (data[glucose_col] <= 150)]
    metrics_arr.append(find_mean_percentage(rangeSecondaryDf, dayCount))

    hypoglycemia1Df = data[data[glucose_col] < 70]
    metrics_arr.append(find_mean_percentage(hypoglycemia1Df, dayCount))

    hypoglycemia2Df = data[data[glucose_col] < 54]
    metrics_arr.append(find_mean_percentage(hypoglycemia2Df, dayCount))

    return metrics_arr

def get_result(data):
    result_row = []
    index = pd.DatetimeIndex(data['Time'])
    wholeday_data = data.set_index('Date')
    dayCount = len(wholeday_data.groupby('Date').count())

    overnight_data = data.iloc[index.indexer_between_time('00:00:00','05:59:59')]
    overnight_results = find_percentage(overnight_data, dayCount)
    result_row += overnight_results

    daytime_data = data.iloc[index.indexer_between_time('6:00:00','23:59:59')]
    daytime_results = find_percentage(daytime_data, dayCount)
    result_row += daytime_results

    wholeday_results = find_percentage(wholeday_data, dayCount)
    result_row += wholeday_results

    n=(1.1+2j)
    result_row.append(n.real)

    return result_row

if __name__ == '__main__':
    cgmDf = read_csv('CGMData.csv', usecols=['Index','Date','Time','Sensor Glucose (mg/dL)'])
    cgmDf['Date'] = pd.to_datetime(cgmDf['Date'])
    cgmDf['time'] = pd.to_datetime(cgmDf['Time']).dt.time

    insulinDf = read_csv('InsulinData.csv', usecols=['Index', 'Date','Time','Alarm'])
    insulinDf['Date'] = pd.to_datetime(insulinDf['Date'])
    insulinDf['time'] = pd.to_datetime(insulinDf['Time']).dt.time

    cgmDf.dropna(subset=[glucose_col], inplace=True)
    cgmDf.reset_index(drop=True, inplace=True)

    insulinAutoIdx = np.flatnonzero(insulinDf['Alarm'] == auto_mode)[-1]
    insulinAutoDate = insulinDf['Date'][insulinAutoIdx]
    insulinAutoTime = insulinDf['Time'][insulinAutoIdx]

    cgmAutoTimeArr = np.flatnonzero(cgmDf['Date'] == insulinAutoDate)

    for i in cgmAutoTimeArr:
        cgmTime = cgmDf["Time"][i]
        if(cgmTime < insulinAutoTime):
            splitIndex = i - 1;
            cgmAutoTime = cgmDf['Time'][i - 1]
            break

    cmgAutoDf = cgmDf.iloc[:splitIndex+1,:]
    cmgAutoDf.reset_index(drop=True, inplace=True)

    cgmManualDf = cgmDf.iloc[splitIndex+1:,:]
    cgmManualDf.reset_index(drop=True, inplace=True)

    manual_mode_results = get_result(cgmManualDf)
    auto_mode_results = get_result(cmgAutoDf)

    result = np.asarray([manual_mode_results, auto_mode_results])
    pd.DataFrame(result).to_csv('Results.csv', header=None, index=None)