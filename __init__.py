import logging
import azure.functions as func
import http.client
import urllib.request
import urllib.parse
import urllib.error
import json
import urllib
import io
from azure.storage.blob import BlockBlobService
from azure.storage.blob import PublicAccess
import requests
import os
import random
from googleapiclient.discovery import build


def main(req: func.HttpRequest) -> func.HttpResponse:
    # signature = request.headers['X-Line-Signature']
    logging.info('Python HTTP trigger function processed a request.')
    try:
        body = req.get_json()
        logging.info(body)
        #User_data.jsonの現在のモードを読み込み
        mode = readfile(body['events'][0]['source']['userId'])
        #ライン返答
        #message_chat(body['events'][0]['replyToken'], body['events'][0]['message']['text'], body['events'][0]['source']['userId'])
        #メッセージ分岐
        if body['events'][0]['message']['type'] == 'location':
            pfile("CODE_MODE_CHAT", body['events'][0]['source']['userId'])
            message_spot(body['events'][0]['replyToken'], body['events'][0]['source']['userId'], body['events'][0]['message']['latitude'], body['events'][0]['message']['longitude'])
        elif body['events'][0]['message']['type'] == 'sticker':
            pfile("CODE_MODE_CHAT", body['events'][0]['source']['userId'])
            message_stamp(body['events'][0]['replyToken'], body['events'][0]['source']['userId'])
        elif body['events'][0]['message']['type'] == 'image':
            pfile("CODE_MODE_CHAT", body['events'][0]['source']['userId'])
            message_image(body['events'][0]['replyToken'], body['events'][0]['source']['userId'], body['events'][0]['message']['id'])
        else:
            if mode=="CODE_MODE_SHOP":
                message_shop(body['events'][0]['replyToken'], body['events'][0]['message']['text'], body['events'][0]['source']['userId'])
            else:        
                message_chat(body['events'][0]['replyToken'], body['events'][0]['message']['text'], body['events'][0]['source']['userId'])
        
    except ValueError as e:
        logging.error('Body Value Error', e.args)
    return func.HttpResponse("{\"statusCode\": 200}", status_code=200)

def message_stamp(replyToken, userId):    
    stickers=[
        {"packageId": "11538","stickerId": "51626521"},
        {"packageId": "11538","stickerId": "51626525"},
        {"packageId": "11538","stickerId": "51626528"},
    ]
    i = random.randint(0, 2)
    messages=[{
        "type": "sticker",
        "packageId": stickers[i]["packageId"],
        "stickerId": stickers[i]["stickerId"]
    }]
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    payload = {
        "replyToken": replyToken,
        "messages":messages
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }
    #ラインにメッセージを送る
    request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
    return

def message_spot(replyToken, userId, LAT, LON):
    l = mapspot(LAT,LON)
    messages=[]
    if len(l)!=0:
        messages.append({})
        messages[0]["type"]="text"
        messages[0]["text"]="ここに行ってみるにゃん！"
        messages.append({})
        messages[1]["type"]="flex"
        messages[1]["altText"]="場所検索"
        contents = []
        for i in range(0,len(l)):
            contents.append(flex_dic(l[i]))
        messages[1]["contents"]={
            "type": "carousel",
            "contents": contents
        }
    elif len(l)==0:
        messages.append({})
        messages[0]["type"]="text"
        messages[0]["text"]="見つからないにゃ～！"
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    payload = {
        "replyToken": replyToken,
        "messages":messages
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }
    #ラインにメッセージを送る
    request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")

def message_shop(replyToken, text, userId):
    r = qnamaker_shop(text)
    logging.info(r)
    answer = r['answers'][0]['answer']
    if answer=="No good match found in KB.":
        messages=[]
        messages.append({})
        messages[0]["type"]="text"
        messages[0]["text"]="よく分かんないにゃ…\nもう一回お願いにゃ！"
    elif answer=="CODE_ESCAPE":
        pfile("CODE_MODE_CHAT", userId)
        messages=[{
            "type":"text",
            "text":"分かったにゃ！\n止めるにゃ～"
        }]
    else:
        pfile("CODE_MODE_CHAT", userId)
        l = yahoo_shop_search(answer)
        messages=[]
        if len(l)!=0:
            messages.append({})
            messages[0]["type"]="text"
            messages[0]["text"]="この商品おすすめにゃん！"
            messages.append({})
            messages[1]["type"]="flex"
            messages[1]["altText"]="商品検索"
            contents = []
            for i in range(0,len(l)):
                contents.append(flex_dic2(l[i]))
            messages[1]["contents"]={
                "type": "carousel",
                "contents": contents
            }
        elif len(l)==0:
            messages.append({})
            messages[0]["type"]="text"
            messages[0]["text"]="見つからないにゃ～！"
    
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    payload = {
        "replyToken": replyToken,
        "messages": messages
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }
    #ラインにメッセージを送る
    request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")

def message_youtube(replyToken):
    messages=[]
    l = youtube_search()
    if len(l)!=0:
        messages.append({})
        messages[0]["type"]="text"
        messages[0]["text"]="オススメ動画にゃ！"
        messages.append({})
        messages[1]["type"]="flex"
        messages[1]["altText"]="オススメ動画にゃ！"
        contents = []
        for dic in l:
            contents.append(flex_dic_youtube(dic))
        messages[1]["contents"]={
            "type": "carousel",
            "contents": contents
        }
    elif len(l)==0:
        messages.append({})
        messages[0]["type"]="text"
        messages[0]["text"]="見つからないにゃ～！"
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    payload = {
        "replyToken": replyToken,
        "messages":messages
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }
    #ラインにメッセージを送る
    request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")

#QnA MakerのG1_SHOP_KBを利用してRESPONSEを受け取る
def qnamaker_shop(text):
    url="https://group1qnamaker.azurewebsites.net/qnamaker/knowledgebases/839274d6-2da6-4272-8461-29adcd6ba82a/generateAnswer"
    headers = {
        'Authorization': 'EndpointKey 7625bf95-f30c-4420-bf30-79a2dddd2a6e',
        'Content-Type': 'application/json'
    }
    question = {'question': text,'top': 1}
    #G1_SHOP_KBのRESPONSE
    r = urllib.request.Request(url, data=json.dumps(question).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(r) as response:
        respose=response.read().decode('utf-8')
        return json.loads(respose)   

def message_chat(replyToken, text, userId):
    #質問をG1_CAT_CHAT01に送り，RESPONSEを受け取る
    r = qnamaker_chat(text)
    #ラインに送るメッセージを抜き出す
    logging.info(r['answers'][0]['answer'])
    
    if(r['answers'][0]['answer']=="No good match found in KB."):
        s = "よく分からないからもう一回言ってにゃ～"
        messages=[{
            "type":"text",
            "text": s
        }]
    #選択がある場合
    elif len(r['answers'][0]["context"]["prompts"])!=0:
        messages=[]
        l = r['answers'][0]['answer'].split("###")
        if "###" in r['answers'][0]['answer']:
            messages=[]
            for i in range(0,len(l)):
                messages.append({})
                messages[i]["type"]="text"
                messages[i]["text"]=l[i]
        else:
            messages.append({})
            messages[0]["type"]="text"
            messages[0]["text"]=r['answers'][0]['answer']
        messages[len(l)-1]["quickReply"]={}
        items=[]
        for i in range(0,len(r['answers'][0]["context"]["prompts"])):
            items.append({})
            items[i]["type"]="action"
            items[i]["action"]={}
            items[i]["action"]["type"]="message"
            items[i]["action"]["label"]=r['answers'][0]["context"]["prompts"][i]['displayText']
            items[i]["action"]["text"]=r['answers'][0]["context"]["prompts"][i]['displayText']
        messages[len(l)-1]["quickReply"]["items"]=items
    # "###"がある場合
    elif "###" in r['answers'][0]['answer']:
        l = r['answers'][0]['answer'].split("###")
        messages=[]
        for i in range(0,len(l)):
            messages.append({})
            messages[i]["type"]="text"
            messages[i]["text"]=l[i]
    else:
        #User_data.jsonの現在のモードを保存
        if(r['answers'][0]['answer']=="CODE_MODE_SHOP"):
            pfile(r['answers'][0]['answer'], userId)
            s = "買いたい商品を入力してにゃん♪"
        else:
            s = r['answers'][0]['answer']
        
        messages=[{
            "type":"text",
            "text": s
        }]
    logging.info(messages)
    #画像表示の場合
    if(r['answers'][0]['answer']=="CODE_MODE_RAND"):
        random_cat(replyToken)

    elif(r['answers'][0]['answer']=="CODE_MODE_YOUTUBE"):
        message_youtube(replyToken)

    #チャットの場合
    else:
        REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
        payload = {
            "replyToken": replyToken,
            "messages":messages
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
        }
        #ラインにメッセージを送る
        request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")

#User_data.jsonから特定のuserIdのモードを読み込む
def readfile(userId):
    f = urllib.request.urlopen('https://blobgroup1.blob.core.windows.net/datacontainer/User_data.json')
    dic = json.load(f)
    f.close()
    if userId not in dic['UserInfo']:
        dic['UserInfo'][userId]='CODE_MODE_CHAT'
        pfile('CODE_MODE_CHAT', userId)
    
    return dic['UserInfo'][userId]

#QnA MakerのG1_CAT_CHAT01を利用してRESPONSEを受け取る
def qnamaker_chat(text):
    url="https://group1qnamaker.azurewebsites.net/qnamaker/knowledgebases/760f1670-d914-4ccc-b7f4-1bbf9fb1559f/generateAnswer"
    headers = {
        'Authorization': 'EndpointKey 7625bf95-f30c-4420-bf30-79a2dddd2a6e',
        'Content-Type': 'application/json'
    }
    question = {'question': text,'top': 1}
    #G1_CAT_CHAT01のRESPONSE
    r = urllib.request.Request(url, data=json.dumps(question).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(r) as response:
        respose=response.read().decode('utf-8')
        return json.loads(respose)

#User_data.jsonに特定のuserIdのモードを書き込む
def pfile(answer, userId):
    f = urllib.request.urlopen('https://blobgroup1.blob.core.windows.net/datacontainer/User_data.json')
    dic = json.load(f)
    dic['UserInfo'][userId] = answer
    #f.write(json.dumps(dic))
    ## Blob 接続準備
    #account_nameにリソース名、account_keyに自分のアクセスキーを入力する
    block_blob_service = BlockBlobService(account_name='blobgroup1', account_key='KcyFmNHRvBwAEtaQ89C6vYFnRN1ftuTGiPcDjV1IOKBxmRmyxfb1ID97ucUNBbkD1BKqB0FgFrmAyC0d/eeThA==')
    # コンテナを作成する
    container_name = "datacontainer"
    block_blob_service.create_container(container_name)
    # コンテナのアクセス権限をpublicに設定する
    block_blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)
    ## ファイルをblobに上げる
    #ファイルストリームを用いてファイルにバイナリデータを書き込む
    text = json.dumps(dic)
    file_data = io.BytesIO(text.encode("UTF-8"))
    #ファイルに名前をつける
    file_name = 'User_data.json'
    #ファイルの書き始め位置を指定（seek(0)は先頭から書き始めるという意味）
    file_data.seek(0)
    #blobを作成する
    block_blob_service.create_blob_from_stream(container_name, file_name, file_data)
    f.close()

def yahoo_shop_search(CODE_SHOP):
    url='https://shopping.yahooapis.jp/ShoppingWebService/V1/json/itemSearch'
    category_id_dic = {
        "日用品": 2508,
        "ファッション": 13457,
        "本": 10002,
        "DVD": 2517,
        "車": 2514,
        "家具":2506,
        "スマホ":2502
                #http://www.webloop.info/yahoo/shop_category/index.php
    }
    keyword_dic ={
        'CODE_SHOP_TSHIRT' :{
            "query":"猫　Tシャツ",
            "category": "ファッション"
        },
        'CODE_SHOP_KUBIWA':{
            "query":"猫　首輪",
            "category": "ファッション"
        },
        'CODE_SHOP_DVD':{
            "query":"猫　DVD",
            "category": "DVD"
        },
        'CODE_SHOP_STECAR_Car':{
            "query":"猫　ステッカー",
            "category": "車"
        },
        'CODE_SHOP_OKIMONO':{
            "query":"猫　置物",
            "category": "家具"
        },
        'CODE_SHOP_KIUUN':{
            "query":"猫　金運",
            "category": "家具"
        },
        'CODE_SHOP_COSU':{
            "query":"猫　コスプレ",
            "category": "ファッション"
        },
         'CODE_SHOP_ANIME':{
            "query":"猫　アニメ",
            "category": "DVD"
        },
        'CODE_SHOP_PACAR':{
            "query":"猫パーカー",
            "category": "ファッション"
        },
        'CODE_SHOP_SUMAHO':{
            "query":"猫スマホケース",
            "category": "スマホ"
        },
        'CODE_SHOP_BENTOU':{
            "query":"猫弁当",
            "category": "日用品"
        },
        'CODE_SHOP_HASI':{
            "query":"猫箸",
            "category": "日用品"
        },
        'CODE_SHOP_SAIHU':{
            "query":"猫財布",
            "category": "ファッション"
        },
        'CODE_SHOP_KASA':{
            "query":"猫 傘",
            "category": "ファッション"
        },
        'CODE_SHOP_ PIASU':{
            "query":"猫　ピアス",
            "category": "ファッション"
        },
        'CODE_SHOP_ NEX':{
            "query":"猫　ネックレス",
            "category": "ファッション"
        },
        'CODE_SHOP_ BAG':{
            "query":"猫　バッグ",
            "category": "ファッション"
        },
        'CODE_SHOP_ KEY':{
            "query":"猫　キーケース",
            "category": "ファッション"
        },
        'CODE_SHOP_MANGA':{
            "query":"猫　漫画",
            "category": "本"
        },
        'CODE_SHOP_BOOK':{
            "query": "猫　雑誌",
            "category": "本"
        },

    }
    query = keyword_dic[CODE_SHOP]["query"]
    category = keyword_dic[CODE_SHOP]["category"]
    category_id = category_id_dic[category]
    
    params={
        'appid' : 'dj00aiZpPVNReG5FUFpRQm5LSCZzPWNvbnN1bWVyc2VjcmV0Jng9MmU-',
        'category_id' : category_id,
        'query' : query,
        'hits': 20
    }
    r = requests.get(url,params=params)
    dic=r.json()
    rec = []
    a=[i for i in range(0,20)]
    
    for i in random.sample(a,3):
        name = (dic["ResultSet"]["0"]["Result"][str(i)]["Name"])
        answer = (dic["ResultSet"]["0"]["Result"][str(i)]["Url"])
        illust = (dic["ResultSet"]["0"]["Result"][str(i)]["Image"]["Medium"])
        catch = (dic["ResultSet"]["0"]["Result"][str(i)]["Description"])
        rec.append({"name":name,"URL":answer,"illust":illust,"catch":catch})
    
    return rec

def mapspot(LAT,LON):
    #試しに動かす用
    #実際はこれらは引数として使われる
    # LAT / LON

    #調べるお店のジャンルをまとめたリスト
    #これをfor文で回してお店を調べる関数を呼び出す
    store_list_survey = [
        {"name" : "ヴィレッジヴァンガード", "industry_code" : "0208002"},
        {"name" : "猫カフェ", "industry_code" : "0115008"},
        {"name" : "猫カフェ", "industry_code" : "0115001"},
        {"name" : "ロフト", "industry_code" : "0207002"},
        {"name" : "ロフト", "industry_code" : "0207010"},
        {"name" : "猫　雑貨", "industry_code" : "0207002"},
        {"name" : "ペットショップ", "industry_code" : "0417003"},
        {"name" : "猫　美術館", "industry_code" : "0305002"},
        {"name" : "猫　神社", "industry_code" : "0424002"},
        {"name" : "猫　神社", "industry_code" : "0424004"},
    ]

    #お店の情報が入った辞書３つを格納したリスト
    store_list_result = []

    #お店の情報が入ったすべての辞書を格納したリスト
    store_list_result_all = []

    #一旦該当するお店をリストにすべて格納する
    for word_dic_survey in store_list_survey:
        tmp = shop_survey(word_dic_survey, LAT, LON)
        store_list_result_all.extend(tmp)
    
    count = 0

    for dic in store_list_result_all:
        count = count + 1

    a=[i for i in range(0, count)]
    for i in random.sample(a, 3):
        tmp = store_list_result_all[i]
        store_list_result.append(tmp)

    return store_list_result

def shop_survey(word_dic_survey, LAT, LON):
    #Yahoo!ローカルサーチAPIのURL
    url = 'https://map.yahooapis.jp/search/local/V1/localSearch'
    #アプリケーションID（商品検索のところでも同じIDを使用している）
    appid = 'dj00aiZpPVNReG5FUFpRQm5LSCZzPWNvbnN1bWVyc2VjcmV0Jng9MmU-'

    #検索結果を一時的にすべて記録するためのリスト
    store_list_survey = [] 

    params = { 
        "appid" : appid,        #アプリケーションID
        "query" : word_dic_survey["name"],        #調べたい言葉（調べたいお店）
        "gc" : word_dic_survey["industry_code"],  #業種コード
        "sort" : "rating",      #お店は星の数順でソートする
        "lat" : LAT,            #中心の緯度
        "lon" : LON,            #中心の経度
        "dist" : 5,             #検索距離(km)を表す
        "output" : "json",      #出力形式を指定する
        "results" : 3           #取得件数を３件にする
    }

    r = requests.get(url, params=params)
    r_json = r.json()
    #pprint.pprint(r_json)

    #条件に当てはまらなかった場合
    if r_json['ResultInfo']['Count'] == 0:
        return store_list_survey
        
        
    #条件に当てはまるお店があった場合
    else:
        r_list = r_json["Feature"]

        for mydict in r_list:
            #print("名前 :" + mydict["Name"])
            #print("住所 :" + mydict["Property"]["Address"])
            url = "https://www.google.com/search?q=" + urllib.parse.quote(mydict["Name"])
            map_url = "https://www.google.co.jp/maps/search/" + urllib.parse.quote(mydict["Name"])
            # url = url.replace(' ', '')
            # url = url.replace('　', '')
            store_dict = {
                "store_name" : mydict["Name"],                      #お店の名前
                "store_adress" : mydict["Property"]["Address"],      #お店の住所
                "store_url": url,    #お店の検索url
                "store_map_url": map_url
            }

            #上の辞書store_dictをリストstore_listに加える
            store_list_survey.append(store_dict)

            #リストの中身を確認するために標準出力している
            #print(store_list_survey)

        return store_list_survey

def random_cat(reply_token):
    url = "https://api.line.me/v2/bot/message/reply"
    channel_access_token = "WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    cat_img_url = requests.get("http://aws.random.cat/meow").json()["file"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+channel_access_token
    }
    data = {
        "replyToken": reply_token ,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": cat_img_url,
                "previewImageUrl": cat_img_url
            }
        ]
    }

    r = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(r) as r:
        response_body = r.read().decode("utf-8")
    
def flex_dic(dic):
    a={
    "type": "bubble",
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
        {
            "type": "text",
            "text": dic['store_name'],
            "wrap": True,
            "weight": "bold",
            "size": "lg",
            "color":"#000000"
        },{
            "type": "box",
            "layout": "vertical",
            "margin": "lg",
            "spacing": "sm",
            "contents": [
            {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                {
                    "type": "text",
                    "text": "住所",
                    "color": "#aaaaaa",
                    "size": "sm",
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": dic['store_adress'],
                    "wrap": True,
                    "color": "#666666",
                    "size": "sm",
                    "flex": 5
                }
                ]
            }
            ]
        }
        ]
    },
    "footer": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
        {
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
            "type": "uri",
            "label": "MAP",
            "uri": dic['store_map_url']
            },
            "color":"#bfff7f",
            "style":"secondary",
        },
        {
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {
            "type": "uri",
            "label": "WEBSITE",
            "uri": dic['store_url']
            },
            "color":"#93c9ff",
            "style":"secondary"
        },
        {
            "type": "spacer",
            "size": "sm"
        }
        ],
        "flex": 0
    },
    "styles": {
        "body": {
            "backgroundColor": "#ffefe0"
        }
    }
    }
    return a

def flex_dic2(dic):
    a={
        "type": "bubble",
        "hero": {
            "type": "image",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "url": dic['illust']
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
            {
                "type": "text",
                "text": dic["name"],
                "wrap": True,
                "maxLines":2,
                "weight": "bold",
                "size": "xl",
                "color": "#111111"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "text",
                    "text": dic['catch'],
                    "wrap": True,
                    "maxLines":3,
                    "weight": "bold",
                    "size": "md",
                    "flex": 0
                }
                ]
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "style": "secondary",
                "action": {
                "type": "uri",
                "label": "詳細",
                "uri": dic['URL']
                },
                "color": "#ffff7f"
            }
            ]
        },
        "styles": {
            "body": {
                "backgroundColor": "#ffefe0"
            }
        }
    }
    return a

def message_image(replyToken, userId, imageId):    
    
    #imageIdから画像バイナリデータを取得する
    img_get_url = "https://api.line.me/v2/bot/message/"+ imageId +"/content"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }

    img_bin = requests.get(img_get_url, headers = headers).content

    #画像バイナリデータをComputerVisionに渡してメッセージを作成
    messages = computervision(img_bin)

    #ラインにメッセージを送る
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    payload = {
        "replyToken": replyToken,
        "messages":messages
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer WaKkwnJ23+9DQ+oiWcXkfU+koKe+0eGHniBNJMaNolc0pTTthZqXAzwGDBrEPUW8LgnNwY8u2q2sQUQxs/DvDDY3gSdzK7SiVbnvg8lB5vP8fAjtbmyFh08yPxBxj8q5Dpxp0FvtBLJWScdVxJiLmQdB04t89/1O/w1cDnyilFU="
    }
    request = urllib.request.Request(REPLY_ENDPOINT, data=json.dumps(payload).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
    return

def computervision(fileBin):
    #引数はバイナリ表現のファイルデータ ex. open(filename, "rb").read()
    
    reactions = {
        "猫": "どこのネコのホネだにゃ！ﾌｼｬｰ！",
        "犬": "イヌとは仲良くなれないのにゃ……",
        "象": "で、でっかいのにゃー！",
        "ネズミ": "待つのにゃ！逃げるにゃ～！",
        "人": "キミもヒトなのにゃ？"
    }

    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': '780869559a024f3691cebb7e1b99376f',
    }

    params = {
        # Request parameters
        'visualFeatures': 'Objects',
        'language': 'en',
    }

    URL = 'https://maiconpyutabijon.cognitiveservices.azure.com/vision/v2.0/analyze'


    response = requests.post(
        URL,
        data = fileBin,
        headers = headers,
        params = params
    )
    
    data = response.json()

    percentage = 0.00
    best_look = "error"

    for obj in data["objects"]:

        obj_per = obj["confidence"]
        #print(obj["object"] + ":" + str(obj_per))

        #更新するか判別している
        if obj_per > percentage:
            best_look = obj["object"]
            percentage = obj_per
    
    messages = []

    if best_look != "error":
        ja_obj = trans(best_look)
        messages.append(
                {
                    "type": "text",
                    "text": "これは" + ja_obj + "だにゃ！"
                }
            )
        if ja_obj in reactions:
            messages.append(
                {
                    "type": "text",
                    "text": reactions[ja_obj]
                }
            )
    else:
        messages.extend([
            {
                "type": "text",
                "text": "よくわからなかったのにゃ……"
            },
            {
                "type": "text",
                "text": "別の写真を送ってほしいにゃ！"
            }
        ])

    return messages



def trans(word):

    endpoint_key = "46228ecd661a42ea8085de7281972497"
    URL = "https://api.cognitive.microsofttranslator.com/translate"

    headers = {
        'Ocp-Apim-Subscription-Key': endpoint_key,
        'Content-Type': 'application/json'
    }

    params = {
        "api-version": 3.0,
        "to": "ja"
    }

    body=[{
        "text": word
    }]

    response = requests.post(
        URL,
        params = params,
        json = body,
        headers = headers
    )

    result_text = response.json()[0]["translations"][0]["text"]
    return result_text

    endpoint_key = "46228ecd661a42ea8085de7281972497"
    URL = "https://api.cognitive.microsofttranslator.com/translate"

    headers = {
        'Ocp-Apim-Subscription-Key': endpoint_key,
        'Content-Type': 'application/json'
    }

    params = {
        "api-version": 3.0,
        "to": "ja"
    }

    body=[{
        "text": word
    }]

    response = requests.post(
        URL,
        params = params,
        json = body,
        headers = headers
    )

    result_text = response.json()[0]["translations"][0]["text"]
    return result_text

def youtube_search():
    YOUTUBE_API_KEY ="AIzaSyBFJf5p88OpFG9lFXjETdrOcP8uVXgP9OE"
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    maxResults = 50
    r = youtube.search().list(
        part='snippet',
        order='date',
        q='猫',
        type='video',
        maxResults = maxResults
    ).execute()
    #pprint.pprint(r)
    rec= []
    i=0
    a = range(0,maxResults)
    for i in random.sample(a,3):
        name=(r['items'][i]['snippet']['title'])  
        url=('https://www.youtube.com/watch?v='+r["items"][i]['id']["videoId"]) 
        illust = (r["items"][i]["snippet"]["thumbnails"]["high"]["url"])
        catch = (r["items"][i]["snippet"]["description"])
        rec.append({"title":name,"description":catch,"URL":url,"thumb_url":illust})
    return(rec)

def flex_dic_youtube(dic):
    a={
        "type": "bubble",
        "hero": {
            "type": "image",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "url": dic['thumb_url']
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
            {
                "type": "text",
                "text": dic["title"],
                "wrap": True,
                "maxLines":2,
                "weight": "bold",
                "size": "xl",
                "color": "#111111"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "text",
                    "text": dic['description'],
                    "wrap": True,
                    "maxLines":3,
                    "weight": "bold",
                    "size": "md",
                    "flex": 0,
                    "color": "#a9a9a9"
                }
                ]
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
            {
                "type": "button",
                "style": "secondary",
                "action": {
                "type": "uri",
                "label": "詳細",
                "uri": dic['URL']
                },
                "color": "#ffff7f"
            }
            ]
        },
        "styles": {
            "body": {
                "backgroundColor": "#ffefe0"
            }
        }
        }

    return a