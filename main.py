import requests,json,random,base64,time
cid = "Qmab3TamGkysC25qiWUU1Xd21YEZzRRsCnzXaZ8agGdUZA"

#计算CID文件大小
def count_files(cid:str,timeout:int = 120)->int:
    try:
        ret = requests.post("http://127.0.0.1:5010/api/v0/object/stat?arg=" + cid,timeout=timeout)
        ret = ret.json()
        return ret["CumulativeSize"]
        #files = ipfs_list(cid,timeout=timeout)
    except requests.exceptions.Timeout:
        return -1

file_size = count_files(cid)
#获得某个CID的叶子块
def get_leaf_block(cid:str):
    url="http://127.0.0.1:5010/api/v0/ls?arg=%s&headers=true&size=true" % cid
    cids = eval(requests.post(url).text)['Objects'][0]['Links']
    return cids
#获得某个CID的所有末端叶子块
def get_extremity_leaf_block_list(cid:str):
    not_leaf_blocks_list = get_leaf_block(cid)
    leaf_blocks_list = []
    while not_leaf_blocks_list:
        i = not_leaf_blocks_list.pop(0)
        if i['Type'] == 1:
            leafs = get_leaf_block(i['Hash'])
            for leaf in leafs:
                not_leaf_blocks_list.append(leaf)
        elif i['Type'] == 2:
            if int(i['Size']) <= 262144:
                if get_leaf_block(i['Hash']) == []:
                    leaf_blocks_list.append(i['Hash'])
                else:
                    leafs = get_leaf_block(i['Hash'])
                    for leaf in leafs:
                        not_leaf_blocks_list.append(leaf)
            else:
                leafs = get_leaf_block(i['Hash'])
                for leaf in leafs:
                    not_leaf_blocks_list.append(leaf)
        else:
            pass
    return leaf_blocks_list
#将末端叶子块转化为Base64形式编码
def get_block_base64(cid:str):
    url="http://127.0.0.1:8080/ipfs/%s" % cid
    data = requests.get(url).content
    return str(base64.b64encode(data),encoding='utf-8')

#奇偶分离Base64编码后的数据用以生成挑战问题与答案
def devide_raw_base64(text:str):
    textl = list(text)
    a_base64_textlist = []
    b_base64_textlist = []
    for n in range(0,len(textl)):
        if (n % 2) == 0:
            a_base64_textlist.append(textl[n])
        else:
            b_base64_textlist.append(textl[n])
    a_base64 = ""
    b_base64 = ""
    for i in a_base64_textlist:
        a_base64 = a_base64 + i
    for q in b_base64_textlist:
        b_base64 = b_base64 + q
    return a_base64,b_base64

#生成挑战内容
def creat_challenge(cid:str)->dict:
    challenge = {}
    challenge['cid'] = cid
    challenge_base64_raw = list(devide_raw_base64(get_block_base64(random.choice(get_extremity_leaf_block_list(cid)))))
    challenge['question'] = random.choice(challenge_base64_raw)
    challenge_base64_raw.remove(challenge['question'])
    challenge['answer'] = challenge_base64_raw[0]
    return challenge

#解题挑战
def answer_challenge(challenge:dict)->str:
    challenge_cid = challenge['cid']
    leaf_blocks = get_extremity_leaf_block_list(challenge_cid)
    true_answer = ""
    while true_answer == "" :
        for block in leaf_blocks:
            answer_raws = list(devide_raw_base64(get_block_base64(block)))
            for i in answer_raws:
                if i == challenge['question']:
                    answer_raws.remove(challenge['question'])
                    true_answer = answer_raws[0]
                else:
                    pass
    return true_answer

#Bench Code
x = 3 #测试次数

n = 1
test_time_list = []
while n <= x:
    print("[Round %s]" % str(n))
    print("生成挑战")
    get_challenge_start_time = time.time()
    challenge = creat_challenge(cid)
    get_challenge_end_time = time.time()
    print("挑战生成完毕，耗时：")
    print(get_challenge_end_time - get_challenge_start_time)
    answer = answer_challenge(challenge)
    answer_time = time.time()
    if answer == challenge['answer']:
        print("挑战验证成功！耗时:")
        print(answer_time - get_challenge_end_time)
        print("计算速度为：")
        print(str(file_size / (answer_time - get_challenge_end_time)) + " Bytes/S")
        test_time_list.append(file_size / (answer_time - get_challenge_end_time))
    else:
        print("挑战验证失败！")
        exit()
    n = n + 1
print("平均计算速度为：")
time_sum = 0
for i in test_time_list:
    time_sum = time_sum +i 
print(str(time_sum/len(test_time_list)) + " Bytes/S")


# print(random.choice(get_extremity_leaf_block_list(cid)))
# for i in get_extremity_leaf_block_list(cid):
#     url="http://127.0.0.1:5010/api/v0/ls?arg=%s&headers=true&size=true" % i
#     if eval(requests.post(url).text)['Objects'][0]['Links'] == []:
#         pass
#     else:
#         print("逻辑验证错误！")
#         print(i)
#         exit()
# print("逻辑验证成功")
    

# json_str = json.dumps(challenge, indent=4) # 缩进4字符
# with open("sample.json", 'w') as json_file:
# 	json_file.write(json_str)

