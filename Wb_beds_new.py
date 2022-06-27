import json
import sys
from os.path import exists as ispath, dirname, basename, join as joinpath, abspath, sep as dirsep,isfile,splitext
sys.path.insert(0, joinpath(dirname(dirname(abspath(__file__)))))
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
import time
import pandas as pd
import helpers as hp
from selenium.webdriver.common.by import By
import datetime
logger = hp.get_logger(__name__)
import pytz
from selenium.webdriver.support.ui import WebDriverWait


search_query = 'https://covidwb.com/'
driver = webdriver.Chrome(executable_path="/Users/radha/Downloads/chromedriver")
driver.get(search_query)
time.sleep(5)
element = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div[3]/div/button')
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

while(True):
   try:
    element.click()
   except StaleElementReferenceException:
     print('need to handle this differently')
     break

time.sleep(5)


Hospital_list=[]
district_list=[]
phoneNumber_list=[]
updated_time_list=[]
beds_avail_list=[]
time_detail = {"timeNumber": [], "category": []}
available_details=[]
results=[]


details_card=driver.find_elements_by_xpath("//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr")
hospital_name=driver.find_elements_by_xpath("//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr/td[1]/div/button/strong")
district_name=driver.find_elements_by_xpath("//span[@class='m-1 p-1 info-chip badge badge-info']")
#phone=driver.find_elements_by_xpath("//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr/td/p[2]/span")
#time=driver.find_elements_by_xpath("//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr/td/p[1]/span")
beds_available=driver.find_elements_by_xpath("//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr/td[3]/span[1]/span")
params ={}
phone_Number=''
lastTime=0.0
i=0

def getUpdatedTimeStamp(lastUpdated):
    values = lastUpdated.split(" ")
    for val in  values:
        if (val.isdigit()):
            time_detail['timeNumber']=val

        elif(val.lower() == 'minutes'):
            time_detail['category'] = 0
        elif (val.lower().find('hours')!=-1):
            time_detail['category'] = 1
        elif (val.lower() == 'day'):
            time_detail['category'] = 2
        elif (val.lower() == 'months'):
            time_detail['category'] = 3


def convertedTimeStamp():
  if(time_detail['category']==0):

      return time.time()*1000- float(time_detail['timeNumber']) *60* 1000
  elif(time_detail['category']==1):

      return time.time()*1000 - float(time_detail['timeNumber'])*60*60* 1000
  elif (time_detail['category'] == 2):

      return time.time()*1000 - float(time_detail['timeNumber']) *24 * 60 * 60 * 1000
  elif (time_detail['category'] == 3):

      return time.time()*1000 - float(time_detail['timeNumber']) *30.44*24* 60 * 60 * 1000



for h in hospital_name:
    Hospital_list.append("Beds available in " +" "+h.text)

    #print(h.text)

for d in district_name:
    district_list.append(d.text)
    #print(d.text)

for beds in beds_available:
    beds_avail_list.append(beds.text)

    #print(beds.text)



for card in hospital_name:
      card.click()

      phone = driver.find_elements_by_xpath(
       "//*[@id='root']/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/table/tbody/tr/td/p[2]/span")


for p in phone:
        #try:
    phoneNumber_list.append(p.text.split(":")[1].replace(' ', '').replace('-', '').replace('.', '').replace('(', '').replace(')', '').replace('/','\n'))
        #except StaleElementReferenceException:

    #print(p.text)


time_list = driver.find_elements_by_css_selector(".border-bottom:nth-child(n) .m-0:nth-child(1) > .text-muted")

for t in time_list:
   getUpdatedTimeStamp(t.text)
   lastTime = convertedTimeStamp()
   updated_time_list.append(lastTime)
   #print(lastTime)

i = 0
for res in beds_avail_list:
     Hospital_list[i] = Hospital_list[i] + " " + res
     i = i + 1


df = pd.DataFrame()

df['description'] = pd.Series(Hospital_list)
df['category'] = "Beds"
df['state'] = "West Bengal"
df['phoneNumber'] =phoneNumber_list
df['District'] = pd.Series(district_list)
df['UpdatedOn'] = pd.Series((updated_time_list),dtype='object')
df.columns = ['description', 'category', 'state','phoneNumber','District', 'UpdatedOn']

mydict = df.to_dict(orient='index')
# print(mydict)
jsonString = json.dumps(mydict, indent=4)
print(jsonString)


df.to_csv('/users/radha/Downloads/wb.beds.csv', index=False, header=True)

driver.close()

driver.quit()

def run():

    last_run = hp.now() - datetime.timedelta(hours=3)
    timestamp = last_run.replace(tzinfo=datetime.timezone.utc).timestamp()
    print(timestamp)

    result_df = (df[df['UpdatedOn'] >= timestamp])
    print(result_df)
    # result_df will have records updated only in last 3 hours
    if len(result_df) != 0:
        for row_dict in result_df.to_dict(orient="records"):
            try:
                hp.send(row_dict)
                pass
            except Exception as e:
                hp.print_error(e)
    else:
        print("skipping records push as no updated data found")
    hp.save('last_run', str(hp.now()))

if __name__ == "__main__":
 run()



