from __future__ import print_function
from asyncio.windows_events import NULL
import os.path
import re
import base64
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
def login(driver):
    driver.implicitly_wait(10)
    #driver.get("https://fantasy.espn.com/basketball/team?leagueId=454844145&teamId=2&statSplit=currSeason")
    driver.get("https://fantasy.espn.com/basketball/team?leagueId=454844145&teamId=2&statSplit=currSeason")
    driver.switch_to.frame("oneid-iframe") #switch to one frame for login 

    username_box = driver.find_element(By.XPATH, '//*[@id="InputIdentityFlowValue"]') #find username box and enter email
    username_box.send_keys("vstrike15@gmail.com")
    driver.find_element(By.XPATH, '//*[@id="BtnSubmit"]').click()

    driver.implicitly_wait(10) #wait 5 seconds if needed and then find password box and enter password
    password_box = driver.find_element(By.XPATH, '//*[@id="InputPassword"]')
    password_box.send_keys('VinayV15')
    driver.find_element(By.XPATH, '//*[@id="BtnSubmit"]').click()

    try:
        driver.find_element(By.XPATH, '//*[@id="recovery-1"]').click() #click on email option to send verification code
        driver.find_element(By.XPATH, '//*[@id="BtnSubmit"]').click() #click submit button for the email option
        time.sleep(12) #wait 10 seconds to get the verification code as email needs to load
        code = getVerificationCode() #get the verification code
        enterCode(code, driver) #enter the code into the code box
    except NoSuchElementException: #if any of these elements arent found, no verification code is needed, so just continue with the program
        pass

    driver.switch_to.default_content() 
def getVerificationCode():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "fantasy basketball automation\credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='from:support@espn.com').execute()
        messages = results.get('messages', [])

        if not messages:
            print('No labels found.')
            return
        
        latest_message = messages[0]
        message = service.users().messages().get(userId='me', id=latest_message['id'], format='full').execute()

        # Extract the message body
        message_data = message['payload']['body']
        body = base64.urlsafe_b64decode(message_data['data']).decode('UTF-8')
        # Find the verification code
        verification_code = body[1970:1976]
        
        return verification_code

    except Exception as e:
        print(f'An error occurred: {e}')
def enterCode(code, driver):
    for i in range(0,6): #iterate from 0-5
        driver.find_element(By.CSS_SELECTOR, f"[data-id='{str(i)}']").send_keys(code[i]) #find data-id from 0 to 5 and send digit at code[i]

    driver.find_element(By.XPATH, '//*[@id="BtnSubmit"]').click() #submit code to move into new window
def formatPlayerText(table):
    table = '\n'.join(table.split('\n')[1:])
    #table = table.replace('\n', ' ')
    table = table.replace('--', 'NO_GAME ---')
    tableList = table.split('\n')
    line = tableList[0] + ";" + tableList[1] + ";TEAM;POSITION;" + tableList[2] + ";" + tableList[3] + ";" + tableList[4] + "\n"
    #slot player team position action opp status
    i = 5
    while (i < len(tableList)):
        if i + 7 > len(tableList):
            break
        if tableList[i + 2] in ['DTD', 'SSPD', 'O']:
            line += tableList[i] + ";" + tableList[i + 1] + " " + tableList[i + 2] + ";" + tableList[i + 3] + ";"
            i += 4
        else:
            line += tableList[i] + ";" + tableList[i + 1] + ";" + tableList[i + 2] + ";"
            i += 3
        line += tableList[i] + ";"
        if tableList[i + 1] not in ['MOVE']:
            line += "----;"
        else:
            line += tableList[i + 1] + ";"
            i += 1
        if tableList[i + 1] in ['NO_GAME ---']:
            line += tableList[i + 1] + "\n"
            i += 2
            continue
        else:
            line += tableList[i + 1] + ";" + tableList[i + 2] + "\n"
            i += 3
    print(line)
    return line
def formatPointText(table):
    table = table.replace('\n', ' ')
    table = table.replace('\'', '')
    tableList = table.split()
    line = ""
    for i in range(len(tableList)):
        if (i % 2) == 1:
            line += tableList[i] + ' '
    return line.split()
def movePG(pg, driver, currentPG):
    print("Point Guards")
    print(pg.sort_values('POINTS', ascending = False))
    if pg.iloc[0,1] != currentPG:
        name = pg.iloc[0,1]
        label = "[aria-label='Select " + name + " to move']"
        label2 = "[aria-label='Confirm move of " + currentPG + " to Point Guard']"
        time.sleep(3)
        driver.find_element(By.CSS_SELECTOR, label).click()
        driver.find_element(By.CSS_SELECTOR,label2).click()
        return name
    return NULL
def moveSG(sg, driver, currentSG):
    print("Shooting Guards")
    print(sg.sort_values('POINTS', ascending = False))
    if sg.iloc[0,1] != currentSG:
        name = sg.iloc[0,1]
        label = "[aria-label='Select " + name + " to move']"
        label2 = "[aria-label='Confirm move of " + currentSG + " to Shooting Guard']"
        time.sleep(3)
        driver.find_element(By.CSS_SELECTOR, label).click()
        driver.find_element(By.CSS_SELECTOR,label2).click()
        return name
    return NULL
def moveSF(sf, driver, currentSF):
    print("Small Forwards")
    print(sf.sort_values('POINTS', ascending = False))
    if sf.iloc[0,1] != currentSF:
        name = sf.iloc[0,1]
        label = "[aria-label='Select " + name + " to move']"
        label2 = "[aria-label='Confirm move of " + currentSF + " to Small Forward']"
        time.sleep(3)
        driver.find_element(By.CSS_SELECTOR, label).click()
        driver.find_element(By.CSS_SELECTOR,label2).click()
        return name
    return NULL
def movePF(pf, driver, currentPF):
    print("Power Forwards")
    print(pf.sort_values('POINTS', ascending = False))
    if pf.iloc[0,1] != currentPF:
        name = pf.iloc[0,1]
        label = "[aria-label='Select " + name + " to move']"
        label2 = "[aria-label='Confirm move of " + currentPF + " to Power Forward']"
        time.sleep(3)
        driver.find_element(By.CSS_SELECTOR, label).click()
        driver.find_element(By.CSS_SELECTOR,label2).click()
        return name
    return NULL
def moveC(c, driver, currentC):
    print("Centers")
    print(c.sort_values('POINTS', ascending = False))
    if c.iloc[0,1] != currentC:
        name = c.iloc[0,1]
        label = "[aria-label='Select " + name + " to move']"
        label2 = "[aria-label='Confirm move of " + currentC + " to Center']"
        time.sleep(3)
        driver.find_element(By.CSS_SELECTOR, label).click()
        driver.find_element(By.CSS_SELECTOR,label2).click()
        return name
    return NULL

    
def main():    
    driver = webdriver.Chrome() #load chrome driver and wait 5 seconds if needed to load website
    login(driver)
    time.sleep(5)

    #table = 'STARTERS NOVEMBER 21\nSLOT\nPLAYER\nACTION\nOPP\nSTATUS\nPG\nJamal Murray\nO\nDen\nPG\nMOVE\n--\nSG\nAustin Reaves\nLAL\nSG, SF\nUtah\n40-297:13 2nd\nSF\nJalen Johnson\nAtl\nSF\nInd\nL 152-157\nPF\nAnthony Davis\nLAL\nPF, C\nUtah\n40-297:13 2nd\nC\nBrook Lopez\nMil\nC\nMOVE\n--\nG\nDamian Lillard\nDTD\nMil\nPG\nMOVE\n--\nF\nPaolo Banchero\nOrl\nPF, SF\nTor\nW 126-107\nUTIL\nJalen Brunson\nNY\nPG, SG\nMOVE\n--\nUTIL\nJulius Randle\nNY\nPF\nMOVE\n--\nUTIL\nChet Holmgren\nOKC\nPF, C\nMOVE\n--\nBench\nJa Morant\nSSPD\nMem\nPG\nMOVE\n--\nBench\nNic Claxton\nBkn\nC, PF\nMOVE\n--\nBench\nBradley Beal\nO\nPhx\nSG, PG\nPor\n87-723:02 3rd\nIR\nEmpty\n--'
    table = driver.find_element(By.XPATH, '//*[@id="fitt-analytics"]/div/div[3]/div/div[3]/div/div/div/div[3]/div/div/div/div/table[1]').text
    data = formatPlayerText(table)
    table = driver.find_element(By.XPATH, '//*[@id="fitt-analytics"]/div/div[3]/div/div[3]/div/div/div/div[3]/div/div/div/div/table[2]/tbody').text
    #table = "'4576.0\n70.4\n3085.5\n40.1\n3611.5\n51.6\n2796.5\n39.4\n3108.0\n45.7\n3612.5\n53.9\n4323.0\n57.6\n4199.0\n70.0\n4307.5\n60.7\n4372.0\n61.6\n3291.0\n65.8\n2730.5\n41.4\n2941.5\n46.7\n--\n--'"
    points = formatPointText(table)
    df = pd.DataFrame([x.split(';') for x in data.split('\n')[1:]], columns=['SLOT', 'PLAYER', 'TEAM', 'POSITION', 'ACTION', 'OPP', 'STATUS'])
    df['POINTS'] = points
    df.drop(13, inplace=True)
    try:
        df = df.loc[~df['ACTION'].str.contains('----')]
    except Exception as e:
        pass
    try:
        df = df.loc[~df['OPP'].str.contains('NO_GAME ---')]
    except Exception as e:
        pass
    try:
       df = df.loc[~df['STATUS'].str.contains('None')]
    except Exception as e:
        pass
    try:
        df = df.loc[~df['STATUS'].isin(['1st', '2nd', '3rd', '4th'])]
    except Exception as e:
        pass

    df.reset_index(drop = True, inplace = True)
    if df.size == 0:
        print("No moves to be made at this time.")
        return
    currentPG = df.iloc[0,1]
    currentSG = df.iloc[1,1]
    currentSF = df.iloc[2,1]
    currentPF = df.iloc[3,1]
    currentC = df.iloc[4,1]
    try:
        df = df.loc[~df['OPP'].str.contains('----')]
    except Exception as e:
        pass
    
    df.reset_index(drop = True, inplace=True)

    print()
    pg = df.loc[(df['POSITION'].str.contains('PG'))]
    pg = pg.loc[~(pg['OPP'].str.contains('----'))]
    pg.reset_index(drop = True, inplace=True)

    sg = df.loc[(df['POSITION'].str.contains('SG'))]
    sg = sg.loc[~sg['OPP'].str.contains('----')]
    sg.reset_index(drop = True, inplace=True)
   
    sf = df.loc[(df['POSITION'].str.contains('SF'))]
    sf = sf.loc[~sf['OPP'].str.contains('----')]
    sf.reset_index(drop = True, inplace=True)

    pf = df.loc[(df['POSITION'].str.contains('PF'))]
    pf = pf.loc[~pf['OPP'].str.contains('----')]
    pf.reset_index(drop = True, inplace=True)
    
    c = df.loc[(df['POSITION'].str.contains('C'))]
    c = c.loc[~c['OPP'].str.contains('----')]
    c.reset_index(drop = True, inplace=True)

    pgSG = df.loc[(df['POSITION'].str.contains('PG|SG', flags = re.I, regex = True))]
    pgSG = pgSG.loc[~pgSG['OPP'].str.contains('----')]


    sfPF = df.loc[(df['POSITION'].str.contains('SF|PF', flags = re.I, regex = True))]
    sfPF = sfPF.loc[~sfPF['OPP'].str.contains('----')]


    playerToRemove = movePG(pg, driver, currentPG) 
    if (playerToRemove in sg['PLAYER'].values):
        sg = sg.drop(sg.index[sg.index[sg['PLAYER'] == playerToRemove].tolist()[0]])

    if (sg.shape[0] > 0):
        playerToRemove = moveSG(sg, driver, currentSG)
        if (playerToRemove in sf['PLAYER'].values):
            sf = sf.drop(sf.index[sf.index[sf['PLAYER'] == playerToRemove].tolist()[0]])
    if (sf.shape[0] > 0):
        playerToRemove = moveSF(sf, driver, currentSF)
        if (playerToRemove in pf['PLAYER'].values):
            pf = pf.drop(pf.index[pf.index[pf['PLAYER'] == playerToRemove].tolist()[0]])
    if(pf.shape[0] > 0):
        playerToRemove = movePF(pf, driver, currentPF)
        if (playerToRemove in c['PLAYER'].values):
            c = c.drop(c.index[c.index[c['PLAYER'] == playerToRemove].tolist()[0]])
    
    if(c.shape[0] > 0):
        playerToRemove = moveC(c, driver, currentC)

    time.sleep(1000)

if __name__ == '__main__':
    main()
