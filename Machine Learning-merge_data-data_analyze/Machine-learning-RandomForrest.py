
#: Importing libraries
import sys
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

#! ENV = 'prep'
#! ENV = 'dev'

ENV = 'prep'

#: Declare constants
path = 'data/'
target = 'Attrition'
#: Loading data
general = pd.read_csv(path + 'general_data.csv')

if ENV == 'dev':
    general = general.sample(frac = 0.10)


#: Eliminate
for c in general:
    if len(general[c].unique()) == 1:
        print(f"Deleting because there is only one {c}")
        del general[c]

del general['MaritalStatus'] # KVKK nedeniyle
#: Mapping
general[target] = general[target].map({'Yes': 1, 'No':0})
general['Gender'] = general['Gender'].map({'Female': 1, 'Male':0})
general['BusinessTravel'] = general['BusinessTravel'].map(
    {'Travel_Rarely': 0.10, 'Travel_Frequently': 0.50, 'Non-Travel': 0.0}
)
general = pd.get_dummies(data = general, columns = ['Department'])
general['EducationField2'] = general['EducationField']
#: Create both dummies and group by mean (target)
vals = dict( general.groupby( by = ['EducationField2'] )[target].mean() )
general['EducationField2'] = general['EducationField2'].map(vals)

general = pd.get_dummies(data = general, columns = ['EducationField'])

vals = dict( general.groupby( by = ['JobRole'] )[target].mean() )
general['JobRole'] = general['JobRole'].map(vals)

#: Fill empty values
#! general['TotalWorkingYears_isnull'] = general['TotalWorkingYears'].isnull()

general['TotalWorkingYears'] = general['TotalWorkingYears'].fillna( general['TotalWorkingYears'].mean() )
general['NumCompaniesWorked'] = general['NumCompaniesWorked'].fillna( general['NumCompaniesWorked'].mean() )

#! Feature transformation
general['MonthlyIncome'] = np.log(general['MonthlyIncome'])

general['DistanceFromHome'] = general['DistanceFromHome'] > 19

#: Pre-analyze
#! for c in general:
#!    print(c, general[c].corr(general[target]))

def findBestRange( df, target, column ):
    maxValue = 0
    maxItem = None
    for i in range(int(df[column].min()), int(df[column].max())):
        df['TEMP'] = df[column] > i
        v = df['TEMP'].corr(df[target])
        if abs(v) > abs(maxValue):
            maxValue = v
            maxItem = i
    return (maxValue, maxItem)

#!for c in general:
#!print( "!", c, general[c].corr(general[target]), findBestRange( general, target, c ) )

#: Merge 
employee_survey = pd.read_csv( path + 'employee_survey_data.csv')
general = pd.merge(general, employee_survey, how='inner', on = 'EmployeeID')
#: Replace NA
general['EnvironmentSatisfaction'] = general['EnvironmentSatisfaction'].replace( 'NA', general['EnvironmentSatisfaction'].mean() )
general['JobSatisfaction'] = general['JobSatisfaction'].replace( 'NA', general['JobSatisfaction'].mean() )
general['WorkLifeBalance'] = general['WorkLifeBalance'].replace( 'NA', general['WorkLifeBalance'].mean() )

"""
#: Merge
general['JobInvolvement'] = general['JobInvolvement'].replace( 'NA', general['JobInvolvement'].mean() )
general['PerformanceRating'] = general['PerformanceRating'].replace( 'NA', general['PerformanceRating'].mean() )
"""

#: Read the in_time csv file
in_time = pd.read_csv(path + 'in_time.csv')
for c in in_time:
    if c != 'EmployeeID':
        in_time[c] = pd.to_datetime( in_time[c] )
        in_time[c] = in_time[c].dt.time

def workingDays( lst: list ):
    wd = 0
    for l in lst:
        if not pd.isnull(l): 
            wd += 1
    return wd

def lateDays( lst: list ):
    ld = 0

    #tenthirty = datetime.time(10, 30, 00)

    for l in lst:
        if not pd.isnull(l): 
            #! if l > tenthirty
            if l.hour > 10 or (l.hour == 10 and  l.minute > 30 ):
                ld += 1
    return ld

#: Read the in_time csv file
out_time = pd.read_csv(path + 'out_time.csv')
for c in out_time:
    if c != 'EmployeeID':
        out_time[c] = pd.to_datetime( out_time[c] )
        out_time[c] = out_time[c].dt.time

WORKING_DAYS = {}
LATE_DAYS = {}
WORKING_HOURS = {}
WORKING_HOURS_TREND = {}



def workingHours( lst1, lst2 ):
    wh = []
    for i in range(len(lst1)):
        lin = lst1[i]
        lout = lst2[i]
        if not pd.isnull(lin): 
            duration = datetime.combine(date.min, lout) - datetime.combine(date.min, lin)
            duration = duration.seconds / 3600
            wh.append( duration )
    return np.mean(wh)



def linreg(X, Y):
	"""
	return a,b in solution to y = ax + b such that root mean square distance between trend line and original points is minimized
	"""
	N = len(X)
	Sx = Sy = Sxx = Syy = Sxy = 0.0
	for x, y in zip(X, Y):
		Sx = Sx + x
		Sy = Sy + y
		Sxx = Sxx + x*x
		Syy = Syy + y*y
		Sxy = Sxy + x*y
	det = Sxx * N - Sx * Sx
	return (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det


def workingHoursTrend( lst1, lst2 ):
    wh = []
    for i in range(len(lst1)):
        lin = lst1[i]
        lout = lst2[i]
        if not pd.isnull(lin): 
            duration = datetime.combine(date.min, lout) - datetime.combine(date.min, lin)
            duration = duration.seconds / 3600
            wh.append( duration )

    m, c = linreg(range(len(wh)), wh)
    return m


for i in range(len(in_time)):
    values = list(in_time.iloc[i].values)
    employee_id = values.pop(0)
    wd = workingDays( values )
    WORKING_DAYS[ employee_id ] = wd

    ld = lateDays( values )
    LATE_DAYS[ employee_id ] = ld


    values2 = list(out_time.iloc[i].values)
    values2.pop(0)

    wh = workingHours( values, values2 )
    WORKING_HOURS[ employee_id ] = wh

    wht = workingHoursTrend( values, values2 )
    WORKING_HOURS_TREND[ employee_id ] = wht
    
#: Combine
general['WorkingDays'] = general['EmployeeID'].map( WORKING_DAYS )
general['LateDays'] = general['EmployeeID'].map( LATE_DAYS )
general['WorkingHours'] = general['EmployeeID'].map( WORKING_HOURS )
general['WorkingHoursTrend'] = general['EmployeeID'].map( WORKING_HOURS_TREND )


general['ConfortZone'] = general['YearsAtCompany'] > 2 # True / False
general['ConfortZone'] = general['ConfortZone'].astype(int) # True => 1 , False = 0


#: Shuffle
general = general.sample(frac = 1.0)

#: Fill na
general = general.fillna(0)

#: Create a new feature from lda 
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
lda = LinearDiscriminantAnalysis()
xx = general.copy()
yy = xx[target]
del xx[target]

lda.fit( xx, yy )
general['LDA_RESULT'] = lda.predict( xx )



#: Save to file
general.to_csv("output.csv", index = False)


#* Use environments below
#* DEV
#* PREP





#: Split
limit = int(len(general) * 0.70)
train = general[:limit]
test = general[limit:]

print("BEFORE, BALANCING",  train.shape)
print("BEFORE, BALANCING", train[target].value_counts())




trainP = train[ train[target] == 1 ]
trainN = train[ train[target] == 0 ]
trainN = trainN.sample(frac = 0.5)

train = pd.concat( [trainP, trainN] )
print("AFTER, BALANCING",  train.shape)
print("AFTER, BALANCING", train[target].value_counts())

train_y = train[target]
del train[target]

test_y = test[target]  # SADECE TARGET KOLONU, 1 kolonluk veri
del test[target] # KALAN TUM KOLONLAR, N kolonluk veri

# PARAMETER OPTIMIZATION (changing parameters of algorithm)
clf = RandomForestClassifier()
clf.fit( train, train_y )
print( "RFC Score : " , clf.score( test, test_y ) )


