import requests, json, time, discord, random
from datetime import datetime, timedelta
from discord import Webhook, RequestsWebhookAdapter
from discord_webhook import DiscordWebhook, DiscordEmbed
import os
from random import randint
from concurrent.futures import ThreadPoolExecutor
import threading

startTime = datetime.now()

def read_skus():
    with open('skus.txt', 'r') as f:   
        line_list = [line.rstrip('\n') for line in f]
    return(line_list)

def task(sku):
    sku = sku
    print("[ + ] The Market - Checking: "+sku)
    time.sleep(5)
    apiurl = f'https://themarket.com/api/search/style?cc=EN&logterms=1&stylecode={read_skus}&merchantid=2&statusid=2%2C3%2C4&lite=0'
    pollapi = requests.get(apiurl)
    data = pollapi.content
    jsonone = json.loads(data)
    
    # Extract Out Current SKU Status
    productname = jsonone['PageData'][0]['SkuName']
    productstatus = str(jsonone['PageData'][0]['IsSoldOut'])
    producturl1 = jsonone['PageData'][0]['WebKey']
    producturl2 = jsonone['PageData'][0]['StyleKey']
    stocknumbers = str(jsonone['PageData'][0]['SkuList'][0]['QtyAts'])
    link = 'https://themarket.com/nz/p/'+producturl1+'/'+producturl2
    price = str(jsonone['PageData'][0]['PriceRetail'])
    
    try:
        imageurl = jsonone['PageData'][0]['ImageDefault']
        thumb = f'https://themarket.azureedge.net/resizer/view?key={imageurl}&b=productimages&w=632&h=632'
    except(Exception):
        thumb = 'https://media.discordapp.net/attachments/605023049640837143/765820231930478592/transparent.png'

    try:
        with open("products/" + sku +".txt", "r") as e:
            previousstock = e.read()
            e.close()
    except(Exception):
        with open("products/" + sku +".txt", "w") as e:
            print("Created New SKU file for "+sku)
            e.write(previousstock)
            e.close()
    
    statuschange = True
    for i in previousstock.splitlines():
        if(str(stocknumbers) == str(previousstock)):
            statuschange = False
            print("No Stock Change for SKU "+sku)
            break  
            
    if(statuschange != False):
        print("Stock Number Change on "+sku+" - New Stock Number "+str(stocknumbers))
        
        with open("products/" + sku +".txt", "w+") as f:
            f.write(str(stocknumbers))
            f.close()
        
        print("Stock Numbers Changed - Sending Webhook")
        user_list = os.listdir("users")
        for file_name in user_list:
            with open("users/" + file_name) as g:
                data = json.load(g)
                color_int = int(data["embed_color"].replace("#", "").replace("0x", ""), 16)
                warehouselink = 'https://www.thewarehouse.co.nz/consoles/'+sku+'.html'+"?utm="+data["utm_code"]
                embed = discord.Embed(title=productname, description="If stock numbers are above zero, may indicate a drop is about to happen (Can be either on The Warehouse or The Market)", url=link+"?utm="+data["utm_code"], color=color_int)
                webhook = Webhook.from_url(data["webhook_url"], adapter=RequestsWebhookAdapter())
                embed.timestamp = datetime.utcnow()
                embed.set_thumbnail(url=thumb)
                embed.set_author(name='The Market - Stock Numbers Changed')
                embed.add_field(name='Previous Stock', value=str(previousstock),inline=True)
                embed.add_field(name='New Stock ', value=str(stocknumbers),inline=True)
                embed.add_field(name='Product Links', value="[The Market]("+link+"?utm="+data["utm_code"]+") | [The Warehouse]("+warehouselink+")", inline=False)
                embed.set_footer(text=data["footer_text"] + " | Console Monitors", icon_url=data["footer_icon"])
                if str(stocknumbers) > '0' and str(stocknumbers) > str(previousstock):
                    webhook.send(embed=embed, username="The Market", avatar_url=data["avatar_url"])

monitoring = True
while monitoring:
    threads = []
    sku_list = read_skus()
    for sku in sku_list:
        sku = sku
        for t_item in threads:
            if "stopped" in str(t_item):
                threads.remove(t_item)
        while len(threads) == 3: 
            time.sleep(3)
            for t_item in threads:
              if "stopped" in str(t_item):
                  threads.remove(t_item)
        thread = threading.Thread(target=task, args=[sku])
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()